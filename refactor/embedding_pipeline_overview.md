# Embedding and Storage Pipeline Overview

This document outlines the files and functionality involved in the process of creating vector embeddings from source data and preparing it for storage in a vector database.

This entire pipeline is executed via standalone command-line scripts and is **completely independent of the live API server**. It does not interfere with the API's ability to handle user queries.

---

### 1. Entry Point: The Embedding Tool

*   **File**: `code/python/tools/compute_embeddings.py`
*   **Functionality**:
    *   This is a command-line script that serves as the starting point for the embedding process.
    *   It reads a JSONL file where each line is a document.
    *   It orchestrates the process of generating an embedding for each document by calling the core embedding service.
    *   Its final output is a new JSONL file where each document is enriched with its corresponding vector embedding. This file is structured to be ready for a database upload script.

### 2. Core Service: Embedding Generation

*   **File**: `code/python/core/embedding.py`
*   **Functionality**:
    *   This file provides a centralized function, `get_embedding`, for generating vector embeddings.
    *   It acts as a dispatcher, reading the configuration to determine which embedding provider (e.g., OpenAI, Azure OpenAI) to use.
    *   It dynamically loads the appropriate client from the `embedding_providers` directory to handle the specific API request. This makes the system modular and easy to extend with new embedding services.

### 3. Provider-Specific Logic: Embedding Clients

*   **Directory**: `code/python/embedding_providers/`
*   **Example File**: `code/python/embedding_providers/openai_embedding.py`
*   **Functionality**:
    *   This directory contains individual modules for each supported embedding service.
    *   Each module is responsible for the specific logic of making an API call to that service, handling authentication, and parsing the response to extract the embedding vector.

### 4. Configuration: Defining Providers

*   **File**: `config/config_embedding.yaml`
*   **Functionality**:
    *   This YAML file defines all available embedding providers and their settings (API keys, models, endpoints).
    *   The `preferred_provider` key determines which provider the `core/embedding.py` service will use by default.

### 5. Storage Logic: The Database Client

*   **File**: `code/python/retrieval_providers/postgres_client.py`
*   **Functionality**:
    *   While not directly called by `compute_embeddings.py`, this file contains the logic for the next step in the pipeline: storing the data.
    *   It contains the `upload_documents` method, which is specifically designed to take the output from the embedding tool and insert it into the PostgreSQL `vector_embeddings` table.
    *   A separate, simple script would be used to read the output file from `compute_embeddings.py` and pass its contents to this `upload_documents` method.

### 6. Configuration: Defining the Database

*   **File**: `config/config_retrieval.yaml`
*   **Functionality**:
    *   This file defines the connection details for the vector database.
    *   The `write_endpoint` key specifies which database configuration to use for all write operations, such as those performed by the `upload_documents` method.
