# NLWeb Azure Web App Deployment

This project has been adapted to run on Azure Web App. This README provides guidance on how to deploy and manage the application in Azure.

## Project Structure

```
code/
├── example-set-keys.sh
├── python
│   ├── app-aiohttp.py
│   ├── app-file.py
│   ├── benchmark
│   │   ├── Benchmark.md
│   │   ├── benchmark_results
│   │   └── run_speed_benchmark.py
│   ├── chat
│   │   ├── cache.py
│   │   ├── conversation.backup
│   │   ├── conversation_debug.py
│   │   ├── conversation.py
│   │   ├── __init__.py
│   │   ├── metrics.py
│   │   ├── participants.py
│   │   ├── schemas.py
│   │   ├── storage.py
│   │   └── websocket.py
│   ├── chatbot_interface.py
│   ├── chat_storage_providers
│   │   ├── __init__.py
│   │   └── memory_storage.py
│   ├── clear_qdrant_conversations.py
│   ├── core
│   │   ├── baseHandler.py
│   │   ├── config.py
│   │   ├── conversation_history.py
│   │   ├── CORE_SUMMARY.md
│   │   ├── embedding.py
│   │   ├── fastTrack.py
│   │   ├── __init__.py
│   │   ├── llm.py
│   │   ├── post_ranking.py
│   │   ├── prompts.py
│   │   ├── query_analysis
│   │   │   ├── analyze_query.py
│   │   │   ├── decontextualize.py
│   │   │   ├── __init__.py
│   │   │   ├── memory.py
│   │   │   ├── query_rewrite.py
│   │   │   ├── relevance_detection.py
│   │   │   └── required_info.py
│   │   ├── ranking.py
│   │   ├── retriever.py
│   │   ├── router.py
│   │   ├── schemas.py
│   │   ├── state.py
│   │   ├── utils
│   │   │   ├── json_utils.py
│   │   │   ├── message_senders.py
│   │   │   ├── nlweb_client.py
│   │   │   ├── trim.py
│   │   │   ├── trim_schema_json.py
│   │   │   └── utils.py
│   │   ├── whoHandler.py
│   │   └── whoRanking.py
│   ├── embedding_providers
│   │   ├── azure_oai_embedding.py
│   │   ├── elasticsearch_embedding.py
│   │   ├── gemini_embedding.py
│   │   ├── __init__.py
│   │   ├── ollama_embedding.py
│   │   ├── openai_embedding.py
│   │   └── snowflake_embedding.py
│   ├── __init__.py
│   ├── llm_calls.jsonl
│   ├── llm_calls_pi_eval.csv
│   ├── llm_providers
│   │   ├── anthropic.py
│   │   ├── azure_deepseek.py
│   │   ├── azure_llama.py
│   │   ├── azure_oai.py
│   │   ├── gemini.py
│   │   ├── huggingface.py
│   │   ├── inception.py
│   │   ├── __init__.py
│   │   ├── llm_calls.jsonl
│   │   ├── llm_provider.py
│   │   ├── ollama.py
│   │   ├── openai.py
│   │   ├── pi_labs.py
│   │   └── snowflake.py
│   ├── methods
│   │   ├── accompaniment.py
│   │   ├── compare_items.py
│   │   ├── conversation_search.py
│   │   ├── cricketLens.py
│   │   ├── cricket_query.py
│   │   ├── ensemble_tool.py
│   │   ├── generate_answer.py
│   │   ├── __init__.py
│   │   ├── item_details.py
│   │   ├── METHODS_SUMMARY.md
│   │   ├── multi_site_query.py
│   │   ├── recipe_substitution.py
│   │   └── statistics_handler.py
│   ├── misc
│   │   ├── embedding.py
│   │   ├── extractMarkup.py
│   │   ├── __init__.py
│   │   ├── json_analysis.py
│   │   ├── logger
│   │   │   ├── logger.py
│   │   │   ├── logging_config_helper.py
│   │   │   ├── set_log_level.py
│   │   │   ├── set_log_level.sh
│   │   │   └── test_logging.py
│   │   ├── nlws.py
│   │   ├── podcast_scraper.py
│   │   ├── postgres_load.py
│   │   └── sample_claude_config.json
│   ├── more_llm_calls.jsonl
│   ├── pi_scoring_comparison.csv
│   ├── README.md
│   ├── requirements-dev.txt
│   ├── requirements.txt
│   ├── retrieval_providers
│   │   ├── azure_search_client.py
│   │   ├── bing_search_client.py
│   │   ├── cf_autorag_client.py
│   │   ├── elasticsearch_client.py
│   │   ├── __init__.py
│   │   ├── milvus_client.py
│   │   ├── opensearch_client.py
│   │   ├── postgres_client.py
│   │   ├── qdrant.py
│   │   ├── qdrant_retrieve.py
│   │   ├── shopify_mcp.py
│   │   ├── snowflake_client.py
│   │   └── utils
│   │       ├── snowflake.py
│   │       └── snowflake.sql
│   ├── storage_providers
│   │   ├── azure_search_storage.py
│   │   ├── elasticsearch_storage.py
│   │   ├── __init__.py
│   │   └── qdrant_storage.py
│   ├── test_dump_qdrant.py
│   ├── testing
│   │   ├── all_tests_example.json
│   │   ├── azure_openai_tests.json
│   │   ├── base_test_runner.py
│   │   ├── check_config.py
│   │   ├── check_connectivity.py
│   │   ├── connectivity
│   │   │   ├── azure_connectivity.py
│   │   │   ├── check_connectivity.py
│   │   │   ├── inception_connectivity.py
│   │   │   └── snowflake_connectivity.py
│   │   ├── embedding
│   │   │   ├── __init__.py
│   │   │   ├── test_elasticsearch_embedding.py
│   │   │   └── test_elasticsearch_embedding.yaml
│   │   ├── end_to_end_tests.json
│   │   ├── end_to_end_tests.py
│   │   ├── __init__.py
│   │   ├── query_retrieval_tests.json
│   │   ├── query_retrieval_tests.py
│   │   ├── query_test_runner.py
│   │   ├── README_database_tests.md
│   │   ├── README.md
│   │   ├── retrieval
│   │   │   ├── 100_scifi_movies_e5_embeddings.ndjson
│   │   │   ├── __init__.py
│   │   │   ├── test_elasticsearch_embedding.yaml
│   │   │   ├── test_elasticsearch_retrieval.py
│   │   │   └── test_elasticsearch_retrieval.yaml
│   │   ├── run_all_tests.bat
│   │   ├── run_all_tests.sh
│   │   ├── run_tests_comprehensive.sh
│   │   ├── run_tests.py
│   │   ├── site_retrieval_tests.json
│   │   ├── site_retrieval_tests.py
│   │   ├── storage
│   │   │   ├── conversations.ndjson
│   │   │   ├── __init__.py
│   │   │   ├── test_elasticsearch_embedding.yaml
│   │   │   ├── test_elasticsearch_storage.py
│   │   │   └── test_elasticsearch_storage.yaml
│   │   ├── test_database_local.py
│   │   ├── test_database_operations.py
│   │   ├── test_database_operations_simple.py
│   │   ├── test_endpoint_results.py
│   │   ├── test_frontend.py
│   │   ├── test_queries_and_rss.py
│   │   ├── test_retrieval_with_endpoint_stats.py
│   │   ├── tests.json
│   │   └── test_with_clean_db.py
│   ├── test_prompt.ipynb
│   ├── test_query.py
│   ├── tests
│   │   ├── test_chat_participants.py
│   │   ├── test_chat_schemas.py
│   │   ├── test_chat_storage.py
│   │   ├── test_chat_websocket.py
│   │   └── test_conversation.py
│   ├── test_shopify_debug.py
│   ├── tools
│   │   ├── compute_embeddings.py
│   │   ├── example_product_focused_description.md
│   │   ├── extract_descriptions.py
│   │   ├── output_5_stores_50urls.jsonl
│   │   ├── output_5_stores_compact.jsonl
│   │   ├── output_5_stores_final.jsonl
│   │   ├── output_5_stores.jsonl
│   │   ├── output_5_stores_no_marketing.jsonl
│   │   ├── output_5_stores_retry.jsonl
│   │   ├── output_cms_detection.jsonl
│   │   ├── output_compact.jsonl
│   │   ├── output_no_marketing.jsonl
│   │   ├── output_test_store_type.jsonl
│   │   ├── remove_embedding_duplicates.py
│   │   ├── remove_url_duplicates.py
│   │   ├── sample_stores.jsonl
│   │   ├── site_description.py
│   │   ├── test_2_stores.jsonl
│   │   ├── test_5_stores.jsonl
│   │   ├── test_bragg_bobs.jsonl
│   │   ├── test_embeddings.jsonl
│   │   ├── test_output_azure.jsonl
│   │   ├── test_output_final.jsonl
│   │   ├── test_output_full.jsonl
│   │   ├── test_output.jsonl
│   │   ├── test_output_timeout.jsonl
│   │   ├── test_output_v2.jsonl
│   │   ├── test_output_v3.jsonl
│   │   ├── test_product_focused.jsonl
│   │   ├── test_stores.jsonl
│   │   └── view_descriptions.html
│   ├── webserver
│   │   ├── a2a_wrapper.py
│   │   ├── aiohttp_server.py
│   │   ├── aiohttp_streaming_wrapper.py
│   │   ├── __init__.py
│   │   ├── mcp_wrapper.py
│   │   ├── middleware
│   │   │   ├── auth.py
│   │   │   ├── cors.py
│   │   │   ├── error_handler.py
│   │   │   ├── __init__.py
│   │   │   ├── logging_middleware.py
│   │   │   └── streaming.py
│   │   ├── README.md
│   │   ├── routes
│   │   │   ├── a2a.py
│   │   │   ├── api.py
│   │   │   ├── chat.py
│   │   │   ├── chat_refactored.py
│   │   │   ├── conversation.py
│   │   │   ├── health.py
│   │   │   ├── __init__.py
│   │   │   ├── mcp.py
│   │   │   ├── oauth.py
│   │   │   └── static.py
│   │   └── WEBSERVER_SUMMARY.md
│   ├── who_calls.jsonl
│   ├── who_calls_pi_eval.csv
│   └── who_trace.jsonl
└── README.md
```