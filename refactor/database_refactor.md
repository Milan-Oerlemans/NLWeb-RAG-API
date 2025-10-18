# Database Refactoring Plan for Multi-Tenancy

## 1. Overview

This document outlines the plan to refactor the `PgVectorClient` and related components to support a multi-tenant database architecture. The core change is to replace the string-based `site` identifier with a `site_id` (UUID) to ensure strict data partitioning between different tenants (sites).

This is a functional and necessary step towards the goals outlined in the main refactoring plan. It isolates data at the database query level, which is critical for security and scalability in a multi-tenant environment.

---

## 2. Update Database Schema

The first step is to update the database schema to support multi-tenancy and enforce data isolation. The table will be renamed to `vector_embeddings` to be more descriptive.

**Action:** Execute the following SQL statement in your PostgreSQL database.

```sql
-- This table will store the vector embeddings for chunks of documents.
CREATE TABLE vector_embeddings (
    embedding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL, -- In sitetor.ai, this will be a foreign key to the indexed_docs table
    site_id UUID NOT NULL,     -- In sitetor.ai, this will be a foreign key to the sites table
    id TEXT NOT NULL,          -- Original document ID from source (e.g., URL hash)
    url TEXT NOT NULL,
    name TEXT NOT NULL,
    schema_json JSONB NOT NULL,
    embedding vector(1536) NOT NULL,
    content TEXT               -- The raw text chunk that was embedded
);

-- Create a unique constraint to prevent duplicate entries for the same document chunk
ALTER TABLE vector_embeddings ADD CONSTRAINT unique_doc_chunk_per_site UNIQUE (id, site_id);

-- Create a vector index for faster similarity searches
CREATE INDEX IF NOT EXISTS embedding_cosine_idx
ON vector_embeddings USING hnsw (embedding vector_cosine_ops);
```

---

## 3. Refactor `code/python/retrieval_providers/postgres_client.py`

This client is the direct interface to the database and requires significant updates.

**Actions:**

*   **Update `__init__`:** The constructor likely uses a `table_name` from the config. This will be updated in a later step.
*   **Modify `search` method:**
    *   Change the method signature from `search(self, query: str, site: Union[str, List[str]], ...)` to `search(self, query: str, site_id: str, ...)`.
    *   Update the `WHERE` clause to filter by `site_id`:
        ```python
        # OLD
        # if sites:
        #     site_placeholders = ", ".join(["%s"] * len(sites))
        #     where_clause = f"WHERE site IN ({site_placeholders})"
        
        # NEW
        if site_id and site_id != "all":
            where_clause = "WHERE site_id = %s"
            params.append(site_id)
        ```
*   **Modify `search_by_url` method:**
    *   Change the method signature to include `site_id`: `search_by_url(self, url: str, site_id: str)`.
    *   Add a `WHERE` clause to filter by `site_id` to prevent users from one site from looking up documents on another.
*   **Modify `upload_documents` method:**
    *   Update the `INSERT` statement to target the `vector_embeddings` table and include the new `site_id` and `document_id` columns.
*   **Modify `delete_documents_by_site` method:**
    *   Rename the method to `delete_documents_by_site_id`.
    *   Update the `DELETE` statement to use `site_id`: `DELETE FROM {self.table_name} WHERE site_id = %s`.

---

## 4. Update Configuration

The retrieval configuration must be updated to point to the new table.

**Action:**

*   In `config/config_retrieval.yaml`, find the configuration block for your PostgreSQL endpoint and update the `index_name` to `vector_embeddings`.

    ```yaml
    # config/config_retrieval.yaml
    endpoints:
      postgres:
        # ... other settings
        index_name: vector_embeddings # <-- UPDATE THIS
        db_type: postgres
    ```

---

## 5. Propagate `site_id` Through the Application Core

The `site_id` must be passed down from the API layer to the data access layer.

**Actions:**

*   **`code/python/webserver/routes/api.py` (`ask_handler`):**
    *   As outlined in the main refactoring plan, an authentication middleware will be responsible for validating an API key and attaching the corresponding `site_id` to the request object.
    *   The `ask_handler` will then extract this `site_id` and inject it into the `query_params` for the `NLWebHandler`.
*   **`code/python/core/baseHandler.py` (`NLWebHandler`):**
    *   Modify the handler to retrieve and use `site_id` instead of `site`.
        ```python
        # OLD
        # self.site = get_param(query_params, "site", str, "all")
        
        # NEW
        self.site_id = get_param(query_params, "site_id", str, None)
        if not self.site_id:
            # Handle error: site_id is required
            raise ValueError("site_id is missing from the request")
        
        # Pass site_id to the search function
        items = await search(
            self.decontextualized_query,
            self.site_id,
            ...
        )
        ```

---

## 6. Remove Data Ingestion Scripts and Update Tests

To finalize the isolation of the RAG API, all data loading responsibilities will be removed, and the test suite must be updated.

**Actions:**

*   **Remove Data Loading Code:** Delete the entire `code/python/data_loading` directory and any other related data ingestion scripts (e.g., `misc/postgres_load.py`).
*   **Update Test Suite:**
    *   Modify all unit and integration tests that interact with the `PgVectorClient`.
    *   Update test fixtures and mock objects to use `site_id` (UUID) instead of `site` (string).
    *   Ensure that tests for the API endpoints correctly simulate the injection of `site_id` by the authentication middleware.