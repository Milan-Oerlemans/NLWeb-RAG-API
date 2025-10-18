# Refactoring Plan: Propagating site_id for PostgreSQL

## 1. Overview

This document outlines the definitive plan to refactor the NLWeb application to use a `site_id` (UUID) for all PostgreSQL database interactions, while using a string representation of that same UUID for all internal application logic, including configuration lookups (prompts and tools).

This approach provides the data integrity and scalability of using UUIDs as primary keys in the database, while preparing the system for a future where users can manage their own prompts based on their site's unique identifier.

## 2. Core Strategy

1.  **Single Source of Truth**: The `api_auth.py` middleware is the entry point. It will authenticate a request via an API key and fetch the corresponding `site_id` (UUID) from the `sites` table in the main PostgreSQL database.

2.  **Dual Representation in Context**: The middleware will inject two versions of the site identifier into the request context:
    *   `request['site_id']`: The raw `UUID` object, to be used exclusively for PostgreSQL queries.
    *   `request['site']`: The `site_id` cast to a string (`str(site_id)`), which will replace the old string-based site name throughout the application's logic.

3.  **Codebase-Wide Refactoring**:
    *   **Database Layer (Postgres)**: All functions interacting with the PostgreSQL vector store (`postgres_client.py`) and conversation history will be modified to accept the `site_id` UUID and use it in `WHERE` clauses.
    *   **Application Logic Layer**: All other parts of the application, including the core handler, prompt/tool lookups, and business logic methods, will be standardized to use the `site` string (which is now the stringified UUID).
    *   **Request Parsing**: The original logic for extracting `site` from query parameters or request bodies will be removed, as the API key is now the sole determinant of the site context.

---

## 3. Step-by-Step Implementation Plan

### Step 1: Enhance Authentication Middleware (`api_auth.py`)

*   **File**: `code/python/webserver/middleware/api_auth.py`
*   **Action**: Modify the `api_key_auth_middleware` to fetch the `site_id` UUID and inject both the UUID and its string representation into the request.
*   **Details**:
    *   The SQL query will be `SELECT site_id FROM sites WHERE api_key = %s`.
    *   Upon successful validation, the middleware will perform:
        ```python
        site_id_uuid = result[0]
        request['site_id'] = site_id_uuid
        request['site'] = str(site_id_uuid)
        ```

### Step 2: Update Core Handler & Remove Old Logic (`baseHandler.py`)

*   **File**: `code/python/core/baseHandler.py`
*   **Action**: Update the `NLWebHandler` to use the new identifiers from the request and remove the old site parsing logic.
*   **Details**:
    *   Modify `NLWebHandler.__init__` to accept `site_id` and `site`. Store them as `self.site_id` and `self.site`.
    *   Search for and **remove** all code that parses the `site` from `query_params` or the request `content`. The site context should now come exclusively from the authentication middleware.

### Step 3: Refactor PostgreSQL Database Interactions

*   **File**: `code/python/retrieval_providers/postgres_client.py`
*   **Action**: Modify all data access functions to filter by the `site_id` UUID.
*   **Details**:
    *   `search()`: Change signature to `search(self, query: str, site_id: UUID, ...)` and update the `WHERE` clause to use `site_id`.
    *   `delete_documents_by_site()`: Change signature to `delete_documents_by_site(self, site_id: UUID, ...)` and update the `WHERE` clause.
    *   `get_sites()`: This function may need to be re-evaluated. It previously returned unique site strings. It should now likely query the main `sites` table, or be deprecated if no longer needed. For now, we will focus on the core RAG flow.

*   **File**: `code/python/storage_providers/` (Specifically for Postgres)
*   **Action**: Update the conversation history storage logic for Postgres to use the `site_id` UUID.
*   **Details**:
    *   Modify methods like `add_conversation` and `get_recent_conversations` to accept and query by `site_id: UUID`.

### Step 4: Standardize Application Logic

*   **Files**: `core/prompts.py`, `core/router.py`, `methods/*.py`, `core/ranking.py`
*   **Action**: Ensure these files consistently use `self.handler.site` (the stringified UUID) for all logic and configuration lookups.
*   **Details**:
    *   No functional change is expected in these files, as they already use the `site` variable. The key is to confirm that the `site` they receive is now the stringified UUID passed down from the handler. The logic `find_prompt(site, ...)` will now attempt to find `<Site id="a1b2c3d4-...">` in the XML, which is the desired behavior.

---

## 4. File-by-File Change Analysis

This table details the required changes across the codebase, focusing on the transition to `site_id` for Postgres.

| File Path | Function/Method | Current Usage of `site` | Required Action |
|---|---|---|---|
| **Authentication & Core** |
| `webserver/middleware/api_auth.py` | `api_key_auth_middleware` | Fetches `site_id` and stores it as a string. | **Modify**: Fetch `site_id` as UUID. Store both `site_id` (UUID) and `site` (string) in the request. |
| `core/baseHandler.py` | `NLWebHandler.__init__` | Parses `site` string from request params/body. | **Modify**: Initialize `self.site_id` and `self.site` from middleware. **Remove** old parsing logic. |
| **Postgres Data Layer** |
| `retrieval_providers/postgres_client.py` | `search` | Accepts `site: str` and uses it in a `WHERE` clause. | **Modify**: Change signature to accept `site_id: UUID`. Update SQL to query `WHERE site_id = %s`. |
| `retrieval_providers/postgres_client.py` | `delete_documents_by_site` | Accepts `site: str`. | **Modify**: Change signature to accept `site_id: UUID`. Update SQL to query `WHERE site_id = %s`. |
| `retrieval_providers/postgres_client.py` | `get_sites` | Returns unique `site` strings from the vector table. | **Deprecate/Modify**: This logic is likely incorrect now. It should query the main `sites` table. Defer for now. |
| `storage_providers/` (Postgres Impl.) | `add_conversation`, `get_recent_conversations` | Uses `site: str` to filter conversation history. | **Modify**: Change signatures to accept `site_id: UUID`. Update SQL to query using the UUID. |
| `misc/postgres_load.py` | (Data Loading Script) | Inserts a `site: str`. | **Modify**: Update script to insert `site_id: UUID` instead. This aligns data loading with the new schema. |
| **Application Logic Layer** |
| `core/prompts.py` | `find_prompt` | Uses `site: str` to look up `<Site id="...">` in `prompts.xml`. | **No Change**: Continue to use `site` (stringified UUID). This is the desired behavior. |
| `core/router.py` | `ToolSelector.__init__` | Uses `handler.site` string to find tools in `tools.xml`. | **No Change**: Continue to use `site` (stringified UUID). |
| `core/ranking.py` | `rankItem` | Uses `site: str` to call `find_prompt`. | **No Change**: Continue to use `site` (stringified UUID). |
| `methods/*.py` | Various | Use `self.handler.site` for logic and prompt lookups. | **No Change**: Continue to use `site` (stringified UUID). |
| **Schemas & Data Structures** |
| `core/schemas.py` | `UserQuery` | Contains `site: Optional[str]`. | **Modify**: Change to `site_id: Optional[UUID]` and remove `site`. Update `from_dict` and `to_dict`. |
| `core/schemas.py` | `ConversationEntry` | Contains `site: str`. | **Modify**: Change to `site_id: UUID`. Update `from_dict` and `to_dict`. |
| `core/schemas.py` | `create_user_message` | Accepts `site: Optional[str]`. | **Modify**: Change to accept `site_id: Optional[UUID]`. |
| **Other Retrieval Providers (For Reference)** |
| `retrieval_providers/*_client.py` | `search`, `delete_documents_by_site` | Use `site: str` for filtering. | **No Change (For Now)**: These are out of scope for the Postgres-only refactor, but they will eventually need similar `site_id` treatment. |

This plan provides a clear and safe path to refactor the application for robust multi-tenancy using `site_id` with PostgreSQL, while setting the stage for the user-managed prompt system.