# Refactoring Plan: Isolating the NLWeb Core RAG API for sitetor.ai

## 1. Introduction

The goal of this refactoring is to isolate the core RAG (Retrieval-Augmented Generation) API from the existing NLWeb project. This will create a self-contained, deployable Docker container for use in other projects, such as `sitetor.ai`. This plan outlines the necessary steps to achieve this, focusing on creating a multi-tenant RAG API that is scalable and secure.

The plan is divided into the following key areas:

1.  **Understand the NLWEB Core:** Analyze the existing codebase to understand the RAG implementation.
2.  **Database Modifications:** Adapt the database schema to support multi-tenancy.
3.  **Isolate the RAG API:** Separate the core API logic from other components like web crawlers.
4.  **Implement Authentication:** Secure the API endpoints.
5.  **Enable Multi-Tenancy:** Ensure data is partitioned by `site_id`.
6.  **Visual Chat Customization:** Plan for a customizable chat interface for different sites.

---

## 2. Understand the NLWEB Core & Site Handling

**Objective:** To gain a deep understanding of the existing RAG API, its components, and how it currently handles requests.

**Action Plan:**

1.  **Analyze Request Flow:**
    *   The `/ask` and `/mcp` endpoints are the main entry points for the RAG API. The routes are defined in `code/python/webserver/routes/api.py` and `code/python/webserver/routes/mcp.py` respectively.
    *   The `ask_handler` in `api.py` and the `mcp_handler` in `mcp.py` both instantiate the `NLWebHandler` class from `core/baseHandler.py` to process requests.
2.  **Identify Core RAG Components:**
    *   **`core/baseHandler.py`:** This is the central orchestrator of the RAG pipeline. The `NLWebHandler` class manages the entire workflow, from query analysis to response generation.
    *   **`core/retriever.py`:** This module handles all interactions with the vector database. The `VectorDBClient` class provides a unified interface for different backends.
    *   **Query Analysis Modules:** The `core/query_analysis` directory contains modules for decontextualization, relevance detection, and other query processing tasks.
    *   **Ranking:** The `core/ranking.py` module is responsible for scoring and ranking the retrieved documents.
    *   **LLM Interaction:** The `core/llm.py` module handles all calls to the Large Language Model.
3.  **Investigate Site Handling:**
    *   The `site` parameter is passed in the API request and is used throughout the RAG pipeline to filter data for a specific site.
    *   The `NLWebHandler` receives the `site` parameter and passes it to the `search` function in `core/retriever.py`.
    *   The `VectorDBClient` then passes the `site` parameter to the specific vector database client (e.g., `PgVectorClient`), which is responsible for including a `WHERE` clause in the database query to filter by site.

---

## 3. PostgreSQL Database Modifications

**Objective:** To adapt the PostgreSQL database to support the multi-tenant architecture required by `sitetor.ai`.

**Action Plan:**

1.  **Adopt `sitetor.ai` Schema:**
    *   The isolated RAG API will be modified to use the `sites` and `indexed_docs` tables as defined in the `sitetor.ai` SQL schema. This will involve updating all database queries to use these new table and column names.
2.  **Create a Vector Storage Table:**
    *   A new table, let's call it `vector_embeddings`, will be created to store the vector embeddings. This table will have the following schema:
        ```sql
        CREATE TABLE vector_embeddings (
            embedding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            document_id UUID NOT NULL REFERENCES indexed_docs(document_id) ON DELETE CASCADE,
            site_id UUID NOT NULL REFERENCES sites(site_id) ON DELETE CASCADE,
            embedding VECTOR(1536), -- Or the appropriate dimension
            content TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        ```
    *   This schema ensures that every vector is linked to a specific document and a specific site, which is crucial for multi-tenancy.
3.  **Update Data Ingestion:**
    *   The data ingestion process (which will be part of `sitetor.ai`, not the isolated RAG API) will need to be updated to populate these new tables. When a document is processed, it should:
        *   Create an entry in the `indexed_docs` table.
        *   Chunk the document content.
        *   For each chunk, generate an embedding and insert it into the `vector_embeddings` table, along with the corresponding `document_id` and `site_id`.

---

## 4. Isolate the RAG API Codebase

**Objective:** To create a new, clean codebase containing only the components essential for the RAG API.

**Action Plan:**

1.  **Identify Essential Code:**
    *   The following directories and files are essential for the RAG API and will be included in the isolated codebase:
        *   `code/python/webserver/`
        *   `code/python/core/`
        *   `code/python/methods/`
        *   `code/python/llm/`
        *   `code/python/retrieval_providers/`
        *   `code/python/prompts/`
        *   `code/python/config/`
        *   `code/python/misc/`
        *   `code/python/app-aiohttp.py`
        *   `code/python/requirements.txt`
    *   The following components are related to web crawling, data ingestion, and the standalone UI, and will be **excluded** from the isolated codebase:
        *   `code/python/scraping/`
        *   `code/python/data_loading/`
        *   `static/`
        *   `demo/`
2.  **Create New Project Structure:**
    *   A new Git repository will be created for the isolated RAG API.
    *   The identified essential files and directories will be copied into this new repository, maintaining their original structure.
3.  **Update Dependencies:**
    *   The `requirements.txt` file will be reviewed and pruned to include only the libraries that are actually used by the isolated API. This will help to keep the Docker image small and secure.

---

## 5. Add Authentication to API Endpoints

**Objective:** To secure the `/ask` and `/mcp` endpoints so that only authorized requests from `sitetor.ai` are processed.

**Action Plan:**

1.  **Implement aiohttp Middleware:**
    *   An `aiohttp` middleware will be created to handle authentication. This middleware will be applied to the `/ask` and `/mcp` routes.
2.  **API Key Extraction:**
    *   The middleware will inspect the incoming request for an `X-API-Key` header.
3.  **Database Validation:**
    *   If the `X-API-Key` header is present, the middleware will perform a database lookup in the `sites` table to find a matching `api_key`.
    *   This will be an asynchronous database query to avoid blocking the event loop.
4.  **Context Injection:**
    *   If a matching site is found, the corresponding `site_id` will be retrieved and attached to the `request` object (e.g., `request['site_id'] = site_id`). This makes the `site_id` available to the API handlers.
5.  **Error Handling:**
    *   If the `X-API-Key` header is missing or if the key is not found in the database, the middleware will return a `401 Unauthorized` HTTP response and stop further processing of the request.

---

## 6. Add Splitting Logic for Multi-Tenancy

**Objective:** To modify the RAG core to use the `site_id` from the authentication step to ensure that it only retrieves data for the correct site.

**Action Plan:**

1.  **Pass `site_id` to Handler:**
    *   The `ask_handler` and `mcp_handler` will retrieve the `site_id` from the `request` object (where the authentication middleware put it).
    *   The `site_id` will then be passed to the `NLWebHandler` during its initialization.
2.  **Propagate `site_id` to Retriever:**
    *   The `NLWebHandler` will pass the `site_id` to the `search` function in `core/retriever.py`.
3.  **Filter by `site_id` in Vector Database:**
    *   The `VectorDBClient` will receive the `site_id` and pass it to the specific vector database client (e.g., `PgVectorClient`).
    *   The `PgVectorClient` will be modified to include a `WHERE site_id = :site_id` clause in all of its SQL queries to the `vector_embeddings` table. This will ensure that the RAG pipeline only has access to the data for the authenticated site.

---

## 7. Understand and Support Visual Chat

**Objective:** To understand how the frontend chat works and how to support customized instances for different sites.

**Action Plan:**

1.  **Analyze Frontend Code:**
    *   The frontend is a vanilla JavaScript application located in the `static` directory. The main files of interest are:
        *   `index.html`: The main entry point for the chat interface.
        *   `chat-interface-unified.js`: The core JavaScript module that handles the chat logic.
        *   `nlweb.js`: A helper module with various utility functions.
    *   The frontend communicates with the backend via the `/ask` endpoint, sending and receiving JSON messages.
2.  **Create a Configuration Endpoint:**
    *   A new API endpoint, `/api/chat/config`, will be created.
    *   This endpoint will be authenticated using the same API key middleware.
    *   It will query the `sites` table for the authenticated site and return the `nlweb` object from the `settings` JSONB column. This object contains the `404_message`, `who_am_i`, and `response_tone`.
3.  **Plan for Frontend Customization:**
    *   The isolated RAG API will not be responsible for hosting the chat frontend. Instead, `sitetor.ai` will host the chat client.
    *   The chat client will be modified to make a request to the `/api/chat/config` endpoint upon initialization.
    *   It will then use the retrieved configuration to customize the chat interface (e.g., display the `who_am_i` message, use the `404_message` when no results are found).
    *   The `response_tone` will be passed as a parameter in the `/ask` request, so the `NLWebHandler` can use it to tailor the LLM's responses.
