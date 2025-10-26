# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""
PostgreSQL Vector Database Client using pgvector - Interface for PostgreSQL operations.
This client provides vector similarity search functionality using the pgvector extension.
Uses psycopg3 for improved async support and performance.
"""

import json
import os
import asyncio
import time
from typing import List, Dict, Union, Optional, Any, Tuple, Set

from urllib.parse import urlparse, parse_qs

# PostgreSQL client library (psycopg3)
import psycopg
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
import pgvector.psycopg

from core.config import CONFIG
from core.retriever import RetrievalClientBase
from core.embedding import get_embedding
from misc.logger.logging_config_helper  import get_configured_logger
from misc.logger.logger import LogLevel
from uuid import UUID

logger = get_configured_logger("postgres_client")

class PgVectorClient(RetrievalClientBase):
    """
    Client for PostgreSQL vector database operations with pgvector extension.
    Provides a unified interface for indexing, storing, and retrieving vector-based search results.
    
    Requirements:
    - PostgreSQL database with pgvector extension installed
    - A configured table with vector type column for embeddings
    """
    
    def __init__(self, endpoint_name: Optional[str] = None):
        super().__init__()  # Initialize the base class with caching
        """
        Initialize the PostgreSQL vector database client.
        
        Args:
            endpoint_name: Name of the endpoint to use (defaults to preferred endpoint in CONFIG)
        """
        self.endpoint_name = endpoint_name or CONFIG.write_endpoint
        self._conn_lock = asyncio.Lock()
        self._pool = None
        self._pool_init_lock = asyncio.Lock()
        
        logger.info(f"Initializing PgVectorClient for endpoint: {self.endpoint_name}")
        
        # Get endpoint configuration
        self.endpoint_config = self._get_endpoint_config()
        self.api_endpoint = self.endpoint_config.api_endpoint
        self.api_key = self.endpoint_config.api_key
        self.database_path = self.endpoint_config.database_path
        self.default_collection_name = self.endpoint_config.index_name or "vector_embeddings"

        self.pg_raw_config = self._get_config_from_postgres_connection_string(self.api_endpoint)
        logger.info(f"PostgreSQL raw config: {self.pg_raw_config}")
        self.host = self.pg_raw_config.get("host")
        self.port = self.pg_raw_config.get("port", 5432)  # Default PostgreSQL port
        self.dbname = self.pg_raw_config.get("database") 
        self.username = self.pg_raw_config.get("username") 
        self.password = self.api_key or self.pg_raw_config.get("password")
        self.table_name = self.default_collection_name or "vector_embeddings"

        # Validate critical configuration
        if not self.host:
            error_msg = f"Missing 'host' in PostgreSQL configuration for endpoint '{self.endpoint_name}'"
            logger.error(error_msg)
            logger.error(f"Available configuration keys: {list(self.pg_raw_config.keys())}")
            raise ValueError(error_msg)
        if not self.dbname:
            error_msg = f"Missing 'database_name' in PostgreSQL configuration for endpoint '{self.endpoint_name}'"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info(f"Using PostgreSQL database: {self.dbname} on {self.host}:{self.port}")
        logger.info(f"Table name: {self.default_collection_name}")
    
    def _get_config_from_postgres_connection_string(self, connection_string: str) -> Dict[str, Any]:
        """
        Parse the PostgreSQL connection string and return a dictionary of configuration parameters.
        This implementation is designed to be robust against special characters in passwords.
        
        Args:
            connection_string: PostgreSQL connection string (e.g., postgresql://user:pass@host:port/db)
        Returns:
            Dictionary of configuration parameters
        """
        logger.info(f"Parsing PostgreSQL connection string")

        try:
            # Remove the scheme prefix if it exists
            if "://" in connection_string:
                rest = connection_string.split("://", 1)[1]
            else:
                rest = connection_string
            
            # Default values
            username, password, host, port, database = None, None, None, None, None

            # Split credentials from the rest of the URI using rsplit to handle '@' in password
            if "@" in rest:
                creds, host_part = rest.rsplit("@", 1)
                
                # Parse credentials
                if ":" in creds:
                    username, password = creds.split(":", 1)
                else:
                    username = creds
            else:
                host_part = rest

            # Parse the rest of the URI (host, port, database)
            # The database is the part after the first slash
            if "/" in host_part:
                host_port, database = host_part.split("/", 1)
                # handle query params
                if "?" in database:
                    database = database.split("?")[0]
            else:
                host_port = host_part
                database = None

            # The host and port are in the host_port part
            if ":" in host_port:
                host, port_str = host_port.split(":", 1)
                port = int(port_str)
            else:
                host = host_port

            config = {
                'host': host,
                'port': port,
                'database': database,
                'username': username,
                'password': password
            }
            logger.info(f"Successfully parsed PostgreSQL connection string. Host: {host}, DB: {database}")
            return config

        except Exception as e:
            logger.warning(f"Manual parsing of PostgreSQL connection string failed: {e}. Falling back to urlparse.")
            # Fallback to the original method if manual parsing fails
            parsed_url = urlparse(connection_string)
            logger.info(f"Parsed PostgreSQL URL (fallback): {parsed_url}")
            
            return {
                'host': parsed_url.hostname,
                'port': parsed_url.port,
                'database': parsed_url.path[1:] if parsed_url.path else None,
                'username': parsed_url.username,
                'password': parsed_url.password
            }

    def _get_endpoint_config(self):
        """
        Get the PostgreSQL endpoint configuration from CONFIG
        
        Returns:
            Tuple of (RetrievalProviderConfig)
        """
        # Get the endpoint configuration object
        endpoint_config = CONFIG.retrieval_endpoints.get(self.endpoint_name)
        
        if not endpoint_config:
            error_msg = f"No configuration found for endpoint {self.endpoint_name}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Verify this is a PostgreSQL endpoint
        if endpoint_config.db_type != "postgres":
            error_msg = f"Endpoint {self.endpoint_name} is not a PostgreSQL endpoint (type: {endpoint_config.db_type})"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Get the raw configuration dictionary from the YAML file
        config_dir = os.path.dirname(os.path.abspath(os.path.join(os.path.dirname(__file__), "../config")))
        config_path = os.path.join(config_dir, "config_retrieval.yaml")

        return endpoint_config
    
    async def _get_connection_pool(self):
        """
        Get or create the connection pool for PostgreSQL.
        Connection pooling is used for better performance and resource management.
        
        Returns:
            A PostgreSQL connection pool
        """
        if self._pool is None:
            async with self._pool_init_lock:
                if self._pool is None:
                    logger.info("Initializing PostgreSQL connection pool")
                    
                    try:
                        # Make sure we have all required connection parameters
                        if not self.host:
                            raise ValueError("Missing host in PostgreSQL configuration")
                        if not self.dbname:
                            raise ValueError("Missing database_name in PostgreSQL configuration")
                        if not self.username:
                            raise ValueError("Missing username or username_env in PostgreSQL configuration")
                        if not self.password:
                            raise ValueError("Missing password or password_env in PostgreSQL configuration")
                            
                        # Log connection attempt (without sensitive information)
                        logger.info(f"Connecting to PostgreSQL at {self.host}:{self.port}/{self.dbname} with user {self.username}")
                        
                        # Set up async connection pool with reasonable defaults
                        conninfo = f"host={self.host} port={self.port} dbname={self.dbname} user={self.username} password={self.password}"
                        self._pool = AsyncConnectionPool(
                            conninfo=conninfo,
                            min_size=1,
                            max_size=10, 
                            open=False # Don't open immediately, we will do it explicitly later
                        )
                        # Explicitly open the pool as recommended in newer psycopg versions
                        await self._pool.open()
                        logger.info("PostgreSQL connection pool initialized")
                        
                        # Verify pgvector extension is installed
                        async with self._pool.connection() as conn:
                            # Register vector type
                            await pgvector.psycopg.register_vector_async(conn)
                            
                            async with conn.cursor() as cur:
                                await cur.execute("SELECT * FROM pg_extension WHERE extname = 'vector'")
                                row = await cur.fetchone()
                                if not row:
                                    logger.warning("pgvector extension not found in the database")
                    
                    except Exception as e:
                        logger.exception(f"Error creating PostgreSQL connection pool: {e}")
                        raise
        
        return self._pool

    async def close(self):
        """Close the connection pool when done"""
        if self._pool:
            await self._pool.close()
    
    async def _execute_with_retry(self, query_func, max_retries=3, initial_backoff=0.1):
        """
        Execute a database query with retry logic for transient failures.
        
        Args:
            query_func: Function that performs the database query
            max_retries: Maximum number of retry attempts
            initial_backoff: Initial backoff time in seconds (doubles with each retry)
            
        Returns:
            Query result
        """
        retry_count = 0
        backoff_time = initial_backoff
        
        while True:
            try:
                # With psycopg3, we can use async directly
                async with (await self._get_connection_pool()).connection() as conn:
                    # Register vector type
                    await pgvector.psycopg.register_vector_async(conn)
                    return await query_func(conn)
            
            except (psycopg.OperationalError, psycopg.InternalError) as e:
                # Handle transient errors like connection issues
                retry_count += 1
                
                if retry_count > max_retries:
                    logger.error(f"Maximum retries exceeded: {e}")
                    raise
                
                logger.warning(f"Database error (attempt {retry_count}/{max_retries}): {e}")
                logger.warning(f"Retrying in {backoff_time:.2f} seconds...")
                
                await asyncio.sleep(backoff_time)
                backoff_time *= 2  # Exponential backoff
            
            except Exception as e:
                # Non-transient errors are raised immediately
                logger.exception(f"Database error: {e}")
                raise
    
    async def delete_documents_by_site(self, site_id: UUID, **kwargs) -> int:
        """
        Delete all documents matching the specified site_id.
        
        Args:
            site_id: Site identifier (UUID)
            **kwargs: Additional parameters
            
        Returns:
            Number of documents deleted
        """
        logger.info(f"Deleting documents for site_id: {site_id}")
        
        async def _delete_docs(conn):
            async with conn.cursor() as cur:
                await cur.execute(
                    f"DELETE FROM {self.table_name} WHERE site_id = %s",
                    (site_id,)
                )
                
                # Get count of deleted rows
                count = cur.rowcount
                await conn.commit()
                return count
        
        try:
            count = await self._execute_with_retry(_delete_docs)
            logger.info(f"Successfully deleted {count} documents for site_id: {site_id}")
            return count
        except Exception as e:
            logger.exception(f"Error deleting documents for site_id {site_id}: {e}")
            raise
    
    async def upload_documents(self, documents: List[Dict[str, Any]], **kwargs) -> int:
        """
        Upload documents to the database.
        Each document should have: id, name, embedding, url, site_id, document_id, and optionally schema_json.
        
        Args:
            documents: List of document objects
            **kwargs: Additional parameters
            
        Returns:
            Number of documents uploaded
        """
        logger.info(f"Uploading {len(documents)} documents")
        
        # Handle empty documents list
        if not documents:
            logger.warning("Empty documents list provided")
            return 0
        
        batch_size = kwargs.get("batch_size", 100)  # Default to 100 docs per batch
        inserted_count = 0
        
        # Process documents in batches for better performance
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            logger.debug(f"Processing batch {i//batch_size + 1} with {len(batch)} documents")
            
            async def _upload_batch(conn):
                async with conn.cursor() as cur:
                    # Prepare the query and values
                    placeholders = []
                    values = []

                    for idx, doc in enumerate(batch):
                        try:
                            # Ensure required fields are present
                            required_fields = ["id", "url", "name", "schema_json", "site_id", "document_id", "embedding", "content"]
                            if not all(k in doc for k in required_fields):
                                missing = [k for k in required_fields if k not in doc]
                                logger.warning(f"Skipping document with missing fields: {missing}")
                                continue

                            # Validate embedding format - should be a list of numbers
                            embedding = doc["embedding"]
                            if not isinstance(embedding, list) or not embedding:
                                logger.warning(f"Skipping document with invalid or empty embedding type: {type(embedding)}")
                                continue
                                
                            if not all(isinstance(x, (int, float)) for x in embedding):
                                logger.warning(f"Skipping document with non-numeric embedding values")
                                continue
                            
                            # Add placeholder for this row
                            placeholders.append("(%s, %s, %s, %s, %s, %s, %s, %s::vector)")
                            
                            # Add values
                            values.extend([
                                doc["id"],
                                doc["url"], 
                                doc["name"],
                                doc["schema_json"],
                                doc["site_id"],
                                doc["document_id"],
                                doc["content"],
                                embedding
                            ])
                            
                        except Exception as e:
                            logger.warning(f"Error processing document {idx} in batch: {e}")
                            continue
                    
                    if not placeholders:
                        logger.warning("No valid documents to insert in batch")
                        return 0
                    
                    # Build and execute the query
                    query = f"""
                        INSERT INTO {self.table_name} (id, url, name, schema_json, site_id, document_id, content, embedding)
                        VALUES {', '.join(placeholders)}
                        ON CONFLICT (id, site_id) DO UPDATE SET
                            url = EXCLUDED.url,
                            name = EXCLUDED.name,
                            schema_json = EXCLUDED.schema_json,
                            document_id = EXCLUDED.document_id,
                            content = EXCLUDED.content,
                            embedding = EXCLUDED.embedding
                    """
                    
                    try:
                        await cur.execute(query, values)
                        count = cur.rowcount
                        await conn.commit()
                        return count
                    except Exception as e:
                        await conn.rollback()
                        logger.error(f"SQL Error: {e}")
                        raise
            
            try:
                batch_count = await self._execute_with_retry(_upload_batch)
                inserted_count += batch_count
                logger.info(f"Batch {i//batch_size + 1} completed: {batch_count} documents inserted/updated")
            except Exception as e:
                logger.exception(f"Error uploading batch {i//batch_size + 1}: {e}")
                raise
        
        logger.info(f"Successfully uploaded {inserted_count} documents")
        return inserted_count
    
    async def search(self, query: str, site_id: UUID, 
                    num_results: int = 50, query_params: Optional[Dict[str, Any]] = None, **kwargs) -> List[List[str]]:
        """
        Search for documents matching the query and site_id.
        
        Args:
            query: Search query string
            site_id: Site identifier (UUID)
            num_results: Maximum number of results to return
            **kwargs: Additional parameters (e.g., similarity_metric)
            
        Returns:
            List of search results, where each result is a list of strings:
            [url, schema_json, name, site_id]
        """
        start_time = time.time()
        logger.info(f"Searching for '{query[:50]}...' in site_id: {site_id}, num_results: {num_results}")
        
        try:
            query_embedding = await get_embedding(query, query_params=query_params)
        except Exception as e:
            logger.exception(f"Error generating embedding for query: {e}")
            raise
        
        similarity_metric = kwargs.get("similarity_metric", "cosine")
        similarity_func = {
            "cosine": "<=>",
            "inner_product": "<#>",
            "euclidean": "<->",
        }.get(similarity_metric, "<=>")
        
        async def _search_docs(conn):
            async with conn.cursor(row_factory=dict_row) as cur:
                where_clause = ""
                params = [query_embedding]
                
                # site_id can be the string "all" for a global search
                if site_id and str(site_id) != "all":
                    where_clause = "WHERE site_id = %s"
                    params.append(site_id)
                
                query_sql = f"""
                    SELECT 
                        name,
                        url,
                        embedding {similarity_func} %s::vector AS similarity_score,
                        site_id,
                        schema_json
                    FROM {self.table_name}
                    {where_clause}
                    ORDER BY similarity_score
                    LIMIT %s
                """
                
                params.append(num_results)
                await cur.execute(query_sql, params)
                rows = await cur.fetchall()
                
                results = []
                for row in rows:
                    result = [
                        row["url"],
                        json.dumps(row["schema_json"], indent=4),
                        row["name"],
                        str(row["site_id"]),
                    ]
                    results.append(result)
                
                return results
        
        try:
            results = await self._execute_with_retry(_search_docs)
            
            end_time = time.time()
            search_duration = end_time - start_time
            
            logger.info(f"Search completed in {search_duration:.2f}s, found {len(results)} results")
            return results
        except Exception as e:
            logger.exception(f"Error in search: {e}")
            raise
    
    async def search_by_url(self, url: str, site_id: UUID, **kwargs) -> Optional[List[str]]:
        """
        Retrieve a document by its exact URL for a specific site.
        
        Args:
            url: URL to search for
            site_id: Site identifier (UUID)
            **kwargs: Additional parameters
            
        Returns:
            Document data or None if not found
        """
        logger.info(f"Retrieving item with URL: {url} for site_id: {site_id}")
        
        async def _search_by_url(conn):
            async with conn.cursor(row_factory=dict_row) as cur:
                query_sql = f"SELECT url, schema_json, site_id, name FROM {self.table_name} WHERE url ILIKE %s AND site_id = %s"
                params = (f"%{url}%", site_id)
                
                await cur.execute(query_sql, params)
                row = await cur.fetchone()
                
                if row:
                    return [row["url"], json.dumps(row["schema_json"], indent=4), row["name"], str(row["site_id"])]
                return None
        
        try:
            result = await self._execute_with_retry(_search_by_url)
            
            if result:
                logger.debug(f"Successfully retrieved item for URL: {url}")
            else:
                logger.warning(f"No item found for URL: {url}")
            
            return result
        except Exception as e:
            logger.exception(f"Error retrieving item with URL: {url}")
            raise
    
    async def search_all_sites(self, query: str, num_results: int = 50, **kwargs) -> List[List[str]]:
        """
        Search across all sites.
        
        Args:
            query: Search query string
            num_results: Maximum number of results to return
            **kwargs: Additional parameters
            
        Returns:
            List of search results
        """
        logger.info(f"Searching across all sites for '{query[:50]}...', num_results: {num_results}")
        return await self.search(query, site_id="all", num_results=num_results, **kwargs)

    async def get_sites(self, **kwargs) -> Optional[List[str]]:
        """
        Get a list of unique site IDs from the PostgreSQL database.
        
        Returns:
            List of unique site IDs as strings
        """
        logger.info("Getting unique site IDs from PostgreSQL")
        
        async def _get_distinct_sites(conn):
            async with conn.cursor() as cur:
                await cur.execute(f"SELECT DISTINCT site_id FROM {self.table_name}")
                rows = await cur.fetchall()
                return [str(row[0]) for row in rows if row[0] is not None]

        try:
            sites = await self._execute_with_retry(_get_distinct_sites)
            logger.info(f"Found {len(sites)} unique site IDs")
            return sites
        except Exception as e:
            logger.exception(f"Error getting unique site IDs: {e}")
            return None
        
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to the PostgreSQL database and return diagnostic information.
        
        Returns:
            Dict with connection status and diagnostic information
        """
        logger.info("Testing PostgreSQL connection")
        
        async def _test_connection(conn):
            result = {
                "success": False,
                "database_version": None,
                "pgvector_installed": False,
                "table_exists": False,
                "document_count": 0,
                "configuration": {
                    "host": self.host,
                    "port": self.port,
                    "database": self.dbname,
                    "username": self.username,
                    "table": self.table_name
                }
            }
            
            try:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT version()")
                    row = await cur.fetchone()
                    result["database_version"] = row[0]
                    result["success"] = True
                    
                    await cur.execute("SELECT * FROM pg_extension WHERE extname = 'vector'")
                    row = await cur.fetchone()
                    result["pgvector_installed"] = row is not None
                    
                    await cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s)", (self.table_name,))
                    row = await cur.fetchone()
                    result["table_exists"] = row[0]
                    
                    if result["table_exists"]:
                        await cur.execute(f"SELECT COUNT(*) FROM {self.table_name}")
                        row = await cur.fetchone()
                        result["document_count"] = row[0]
                        
            except Exception as e:
                logger.exception("Error testing PostgreSQL connection")
                result["error"] = str(e)
                
            return result
        
        try:
            return await self._execute_with_retry(_test_connection)
        except Exception as e:
            logger.exception("Failed to test PostgreSQL connection")
            return {"success": False, "error": str(e)}

    async def check_table_schema(self) -> Dict[str, Any]:
        """
        Check if the database table schema is correctly set up.
        
        Returns:
            Dict with table schema information
        """
        logger.info(f"Checking table schema for {self.table_name}")
        
        async def _check_schema(conn):
            schema_info = {
                "table_exists": False,
                "columns": {},
                "needs_corrections": []
            }
            
            try:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s)", (self.table_name,))
                    row = await cur.fetchone()
                    schema_info["table_exists"] = row["exists"]
                    
                    if not schema_info["table_exists"]:
                        schema_info["needs_corrections"].append(f"Table '{self.table_name}' does not exist.")
                        return schema_info
                    
                    await cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s", (self.table_name,))
                    columns = await cur.fetchall()
                    for col in columns:
                        schema_info["columns"][col["column_name"]] = col["data_type"]
                    
                    required_columns = {
                        "embedding_id": "uuid",
                        "document_id": "uuid",
                        "site_id": "uuid",
                        "id": "text",
                        "url": "text",
                        "name": "text",
                        "schema_json": "jsonb",
                        "embedding": "vector",
                        "content": "text"
                    }
                    
                    for col_name, col_type in required_columns.items():
                        if col_name not in schema_info["columns"]:
                            schema_info["needs_corrections"].append(f"Missing required column '{col_name}' of type '{col_type}'")
                        elif col_type not in schema_info["columns"][col_name]:
                             schema_info["needs_corrections"].append(f"Column '{col_name}' has wrong type. Expected '{col_type}', found '{schema_info['columns'][col_name]}'")

            except Exception as e:
                logger.exception(f"Error checking table schema: {e}")
                schema_info["error"] = str(e)
            
            return schema_info
        
        try:
            return await self._execute_with_retry(_check_schema)
        except Exception as e:
            logger.exception(f"Failed to check table schema: {e}")
            return {"error": str(e)}
