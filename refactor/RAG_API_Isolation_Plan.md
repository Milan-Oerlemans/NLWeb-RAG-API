# RAG API and Chat API Isolation Plan

## 1. Introduction

This document outlines the plan to isolate the core RAG (Retrieval-Augmented Generation) and Chat APIs from the NLWeb project. The goal is to create a lean, focused codebase that can be containerized and deployed as a standalone service for projects like `sitetor.ai`. This plan details all the files, directories, and code components that should be removed to eliminate functionality related to data scraping, database loading, command-line interface (CLI) tools, and the frontend user interface.

---

## 2. Guiding Principles

-   **Retain Core API:** Keep all code essential for the `/ask`, `/mcp`, and the new `/api/chat/config` endpoints.
-   **Remove Data Ingestion:** All functionality for scraping, parsing, and loading data into the database will be removed. This will be the responsibility of the consuming application (e.g., `sitetor.ai`).
-   **Remove Frontend UI:** The entire `static` directory and all related HTML/CSS/JS files will be removed. The API will be headless.
-   **Remove CLI Tools:** All standalone scripts and CLI tools will be removed. The project will be interacted with solely through its API endpoints.
-   **Simplify Project Root:** The root directory will be cleaned of all non-essential scripts and configuration files.

---

## 3. Files and Directories to be Removed

The following is a comprehensive list of all files and directories that should be removed from the project, categorized by their function.

### 3.1. Frontend UI and Static Assets

These files are all related to the user-facing chat interface and are not needed for a headless API.

-   **Directory:** `static/`
    -   **Reason:** Contains all frontend assets, including HTML, CSS, JavaScript, and images for the chat UI.
-   **File:** `debug_auth.html`
    -   **Reason:** A standalone HTML file for debugging authentication, not part of the core API.
-   **File:** `web.config`
    -   **Reason:** Configuration for IIS, typically for deploying on Windows servers, and includes rules for serving static files. Not needed for the Dockerized API.

### 3.2. Data Ingestion and Database Loading

This functionality will be handled by the `sitetor.ai` project. The RAG API will only be responsible for retrieving data from an already-populated database.

-   **Directory:** `code/python/data_loading/`
    -   **Reason:** Contains all scripts for loading data into vector databases (e.g., `db_load.py`).
-   **Directory:** `code/python/misc/`
    -   **Reason:** Contains miscellaneous scripts, including `postgres_load.py` for setting up the database schema. This will be managed by `sitetor.ai`.
-   **Directory:** `data/`
    -   **Reason:** Contains sample data files for testing data loading.

### 3.3. CLI Tools and Standalone Scripts

These are scripts intended for direct execution from the command line, not for serving API requests.

-   **Directory:** `scripts/`
    -   **Reason:** Contains various utility and testing scripts, including the `nlweb` CLI.
-   **File:** `check_dependencies.py`
    -   **Reason:** A script to check for required system dependencies. This can be handled by the `Dockerfile`.
-   **File:** `code/python/app-file.py`
    -   **Reason:** An alternative file-based server, not needed for the main API.
-   **File:** `code/python/chatbot_interface.py`
    -   **Reason:** A command-line interface for chatting with the bot.
-   **File:** `code/python/clear_qdrant_conversations.py`
    -   **Reason:** A script for clearing conversations from a Qdrant database.
-   **File:** `setup.sh`
    -   **Reason:** A setup script for the CLI and local environment.
-   **File:** `startup.sh` and `startup_aiohttp.sh`
    -   **Reason:** These are startup scripts for running the server. The Docker container will have its own entrypoint command, making these redundant.
-   **File:** `start_server_debug.py`
    -   **Reason:** A script for starting the server in debug mode. This can be configured in the Docker entrypoint if needed.

### 3.4. Testing and Validation Artifacts

These files are used for testing queries and validating results, but are not part of the core application logic. The core unit and integration tests in the `tests/` directory will be kept and adapted.

-   **File:** `all_good_queries.txt`
-   **File:** `batch2_good_queries.txt`
-   **File:** `query_test_results_batch2.json`
-   **File:** `query_test_results.json`
-   **File:** `test_queries_200.txt`
-   **File:** `test_queries_batch2.txt`
-   **File:** `test_who_queries.sh`
-   **File:** `top_100_queries.txt`
-   **File:** `validate_who_queries.py`
-   **File:** `warm_up_who_cache.py`
-   **File:** `who_queries_validation.txt`
-   **File:** `who_validation_results.txt`
-   **File:** `code/python/llm_calls_pi_eval.csv`
-   **File:** `code/python/llm_calls.jsonl`
-   **File:** `code/python/more_llm_calls.jsonl`
-   **File:** `code/python/pi_scoring_comparison.csv`

### 3.5. Documentation and Examples

The documentation will need to be significantly updated. Many of the existing documents are related to the features being removed.

-   **Directory:** `docs/`
    -   **Reason:** While some documents will be kept and updated (e.g., `nlweb-rest-api.md`), many are related to setup, CLI, and data loading and will be removed. A full review is required, but the following are clear candidates for removal:
        -   `nlweb-cli.md`
        -   `nlweb-hello-world.md`
        -   `setup-*.md` (all setup guides for different backends will be consolidated into the new `README.md`)
        -   `tools-database-load.md`
-   **Directory:** `demo/`
    -   **Reason:** Contains demo files, which are not part of the core API.
-   **Directory:** `images/`
    -   **Reason:** Contains images used in the documentation, most of which will become irrelevant.

### 3.6. Miscellaneous Project Files

-   **File:** `.github/workflows/codeql.yml`
    -   **Reason:** This can be kept, but may need to be re-evaluated for the new, smaller codebase.
-   **File:** `.vscode/launch.json`
    -   **Reason:** Developer-specific editor configuration.
-   **File:** `azure-app-service-config.txt` and `azure-web-config.txt`
    -   **Reason:** Specific to Azure App Service deployments. The primary deployment target will be a Docker container, making these unnecessary.
-   **File:** `deploy_azure_webapp.sh`
    -   **Reason:** Deployment script for Azure Web Apps.
-   **File:** `refactoring_plan.md`
    -   **Reason:** This is a planning document and not part of the final application.
-   **File:** `code/example-set-keys.sh`
    -   **Reason:** An example script for setting environment variables. The `.env.template` is sufficient.

---

## 4. Files and Directories to be Kept and Refactored

The following components are essential to the RAG and Chat APIs and will be kept. They will, however, require refactoring to support the new multi-tenant architecture.

-   **Directory:** `code/python/`
    -   `app-aiohttp.py`: The main application entry point.
    -   `webserver/`: The `aiohttp` server, routes, and middleware. **(Refactor: Add authentication middleware).**
    -   `core/`: The core RAG pipeline. **(Refactor: Pass `site_id` through the pipeline).**
    -   `methods/`: Specialized query handlers (tools).
    -   `llm_providers/`: LLM provider wrappers.
    -   `retrieval_providers/`: Vector database clients. **(Refactor: Update queries to filter by `site_id` and use the new `sitetor.ai` schema).**
-   **Directory:** `config/`
    -   All YAML configuration files, `prompts.xml`, and `tools.xml`. These will be kept as they define the behavior of the RAG pipeline.
-   **Directory:** `tests/`
    -   Unit and integration tests will be adapted for the new architecture. End-to-end tests that rely on the UI will be removed.
-   **File:** `Dockerfile`, `docker-compose.yaml`, `.dockerignore`
    -   These will be the primary method for building and running the application.
-   **File:** `requirements.txt`
    -   Will be pruned to include only necessary dependencies.
-   **File:** `.env.template`
    -   Will be updated to reflect the required environment variables for the isolated API.
-   **File:** `README.md`
    -   Will be rewritten to document the new, isolated API.

---

## 5. Conclusion

By following this plan and removing the components listed above, we will create a clean, isolated, and maintainable codebase for the core RAG and Chat APIs. This will provide a solid foundation for the `sitetor.ai` project and other future applications.
