# NLWeb Project Overview

## 1. High-Level Description

NLWeb is a framework for building conversational interfaces for websites, leveraging existing Schema.org markup to create natural language understanding capabilities. It is designed to be a foundational layer for the "AI Web," enabling both human and AI agent interactions through a simple protocol and open-source tools. The project is platform-agnostic, supporting a wide range of operating systems, vector stores, and large language models (LLMs).

The core idea is to use the structured data already present on many websites (in formats like RSS and Schema.org) to power a retrieval-augmented generation (RAG) system. This allows for the creation of chatbots and other conversational tools that are grounded in the website's actual content, reducing hallucinations and providing more accurate responses.

## 2. Architecture and Flow

The system follows a multi-stage process to handle user queries, as detailed in the "Life of a Chat Query" documentation. The key steps are:

1.  **Query Reception:** The web server receives a user's query.
2.  **Pre-retrieval Analysis:** A series of parallel LLM calls are made to:
    *   Check the query's relevance to the site's content.
    *   Decontextualize the query based on conversation history.
    *   Detect if the user is asking the system to remember information.
    *   Determine if more information is needed from the user.
3.  **Tool Selection:** Based on the query and the available tools defined in `tools.xml`, the system selects the most appropriate tool to handle the request. This could be a simple search, a request for item details, a comparison, or a more complex "ensemble" query that combines multiple pieces of information.
4.  **Retrieval:** The selected tool queries one or more vector databases to retrieve relevant documents or data. The system supports concurrent queries to multiple backends.
5.  **Ranking:** The retrieved results are scored and ranked by an LLM to determine their relevance to the user's query.
6.  **Post-processing (Optional):** The ranked results can be summarized or used to generate a direct answer to the user's question.
7.  **Response:** The final results are sent back to the user, typically in a streaming fashion.

## 3. Key Technologies and Frameworks

*   **Backend:** Python (primarily using asyncio for concurrency)
*   **Frontend:** JavaScript (ES6 classes, module pattern)
*   **Web Server:** aiohttp
*   **Configuration:** YAML files for configuring LLMs, retrieval endpoints, and other settings.
*   **Data Ingestion:** Supports RSS/Atom feeds, JSON, and CSV files.
*   **Vector Stores:**
    *   Qdrant
    *   Snowflake
    *   Milvus
    *   Azure AI Search
    *   Elasticsearch
    *   Postgres (with pgvector)
    *   Cloudflare AutoRAG
*   **LLMs:**
    *   OpenAI
    *   DeepSeek
    *   Gemini
    *   Anthropic
    *   Inception
    *   HuggingFace
    *   Ollama

## 4. Key Files and Directories

*   `code/python/app-aiohttp.py`: The main entry point for the web application.
*   `config/`: This directory contains all the YAML configuration files for the application, including:
    *   `config_llm.yaml`: For configuring LLM providers.
    *   `config_retrieval.yaml`: For configuring vector database endpoints.
    *   `config_embedding.yaml`: For configuring embedding providers.
    *   `tools.xml`: For defining the available tools and their behavior.
    *   `prompts.xml`: Contains the prompts used for various LLM calls.
*   `code/python/core/`: Contains the core logic of the application, including the base handler, retriever, and ranking components.
*   `code/python/llm/`: Contains the wrappers for different LLM providers.
*   `code/python/retrieval/`: Contains the clients for different vector database backends.
*   `code/python/tools/`: Contains various data loading and processing tools.
*   `static/`: Contains the frontend JavaScript, HTML, and CSS files for the user interface.
*   `docs/`: Contains all the project documentation.

## 5. Local Setup and Running the Project

1.  **Prerequisites:** Python 3.10+
2.  **Clone the repository.**
3.  **Create and activate a virtual environment.**
4.  **Install dependencies:** `pip install -r requirements.txt`
5.  **Configure the application:**
    *   Copy `.env.template` to `.env` and add the necessary API keys and endpoints for your chosen LLM and vector store.
    *   Update the `config/*.yaml` files to specify your preferred providers.
6.  **Load data:** Use the `db_load.py` script to load data from a source (e.g., an RSS feed) into your vector database.
7.  **Run the server:** `python code/python/app-aiohttp.py`
8.  **Access the UI:** Open `http://localhost:8000` in your browser.

The project also provides a CLI for simplified configuration and execution, which can be accessed by running `source setup.sh`.

## 6. Project-Specific Conventions

*   **Python:**
    *   `snake_case` for files, modules, functions, and variables.
    *   `PascalCase` for classes.
    *   Type hints are used for function signatures.
    *   Async/await is preferred for I/O operations.
*   **JavaScript:**
    *   `kebab-case` for files.
    *   `PascalCase` for classes.
    *   `camelCase` for methods, functions, and variables.
    *   ES6 classes and modules are used.
*   **Configuration:**
    *   YAML files are used for structured configuration.
    *   Environment variables are used for secrets.
*   **Logging:**
    *   Structured logging is used with different log levels.
    *   Sensitive data is not logged.
Ok 