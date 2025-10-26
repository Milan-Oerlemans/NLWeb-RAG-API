# NLWeb Logging System

The NLWeb application employs a robust and configurable logging system built on Python's standard `logging` module, with several enhancements for performance and ease of use. This document provides an overview of its architecture, configuration, and usage.

## Key Features

- **Configuration-driven:** Logging behavior is controlled via a central YAML file (`config/config_logging.yaml`), allowing for easy adjustments without code changes.
- **Asynchronous by Default:** Log messages are processed by a background thread to minimize I/O blocking in the main application, improving performance.
- **Module-specific Levels:** You can set different log verbosity levels for different parts of the application (e.g., make the LLM wrapper more verbose while keeping other components quiet).
- **Dynamic Level Control:** Utility scripts are provided to change log levels across the entire application on the fly for easier debugging.
- **Environment Variable Integration:** Key settings like log output directories and configuration paths can be controlled via environment variables.
- **Request/Response Logging:** A dedicated middleware in the `aiohttp` web server logs all incoming requests and their corresponding responses.

## Core Components

The logging system is primarily composed of two key files located in `code/python/misc/logger/`:

1.  `logger.py`: This file contains the `LoggerUtility` class, a wrapper around the standard Python logger that adds features like file rotation and console output.
2.  `logging_config_helper.py`: This is the main engine for the logging system. It handles:
    *   Loading and parsing the `config/config_logging.yaml` file.
    *   Creating `LazyLogger` instances that are initialized only when first used.
    *   Managing the `AsyncLogProcessor`, a background thread that queues and writes log messages asynchronously.

## Configuration

The entire logging system is configured through `config/config_logging.yaml`. This file defines the default behavior and allows for specific overrides for each module.

### Key Configuration Sections:

-   `default_level`: The global log level (e.g., `INFO`, `DEBUG`, `ERROR`) to use if a module doesn't specify its own.
-   `log_directory`: The directory where log files will be stored. This can be overridden by the `NLWEB_OUTPUT_DIR` environment variable.
-   `global`: Settings that apply to all loggers, such as the log message format and whether to output to the console and/or files.
-   `modules`: This section allows you to define specific configurations for different parts of the application. Each key is a module name, and you can set a specific `default_level`, `log_file`, and the `env_var` to control its level.

### Environment Variables

-   `NLWEB_OUTPUT_DIR`: If set, the logging system will create a `logs` subdirectory within this path and store all log files there. This is the recommended way to control log file location.
-   `NLWEB_CONFIG_DIR`: If set, the system will look for `config_logging.yaml` in this directory.
-   Module-specific variables (e.g., `LLM_LOG_LEVEL`, `RANKING_LOG_LEVEL`): These can be set to override the log level for a specific module at runtime.

## Usage

To use the logger within any Python module, import and call the `get_configured_logger` function.

```python
# In any module, e.g., code/python/llm/llm_base.py
from code.python.misc.logger import get_configured_logger

# Get a logger instance named after the module
# The name should match a key in the `modules` section of the config
logger = get_configured_logger("llm_wrapper")

# Log messages at different levels
logger.debug("This is a detailed debug message.")
logger.info("An informational message about an operation.")
logger.warning("Something unexpected happened, but it's not a critical error.")
logger.error("A serious error occurred.")
logger.exception("An exception was caught, logging with stack trace.")
```

## Changing Log Levels

For debugging, it's often necessary to change the verbosity of the logs. The project includes scripts to make this easy.

### Using the Shell Script (Recommended for Linux/macOS)

The `set_log_level.sh` script sets the environment variables for all configured loggers in your current shell session.

**Important:** You must `source` the script for it to work correctly.

```bash
# To set all loggers to DEBUG level
source code/python/misc/logger/set_log_level.sh DEBUG

# To set all loggers back to INFO
source code/python/misc/logger/set_log_level.sh INFO
```

### Using the Python Script

Alternatively, you can use the `set_log_level.py` script. This script will print the `export` commands that you can then copy and paste into your terminal.

```bash
python code/python/misc/logger/set_log_level.py DEBUG
```

This will output a series of `export` commands that you can run to apply the changes.

## Web Server Logging

The file `code/python/webserver/middleware/logging_middleware.py` sets up a middleware for the `aiohttp` web server. This middleware automatically logs key information for every HTTP request that the server receives, including:

-   Request method and path (`GET /chat`)
-   Response status code (`200 OK`)
-   Total time taken to process the request
-   Request headers (with sensitive information like `Authorization` removed)

This provides a high-level overview of server traffic and performance.
