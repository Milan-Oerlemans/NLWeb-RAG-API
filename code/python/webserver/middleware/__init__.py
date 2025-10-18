"""Middleware package for aiohttp server"""

from .cors import cors_middleware
from .error_handler import error_middleware
from .logging_middleware import logging_middleware
from .auth import auth_middleware
from .api_auth import api_key_auth_middleware, create_main_db_pool, close_main_db_pool
from .streaming import streaming_middleware


def setup_middleware(app):
    """Setup all middleware in the correct order"""
    # Note: Middleware is applied in reverse order
    # So the first in this list is the outermost (executes first)
    app.middlewares.append(error_middleware)
    app.middlewares.append(logging_middleware)
    app.middlewares.append(cors_middleware)
    app.middlewares.append(api_key_auth_middleware)
    app.middlewares.append(auth_middleware)
    app.middlewares.append(streaming_middleware)


__all__ = [
    'setup_middleware',
    'cors_middleware',
    'error_middleware',
    'logging_middleware',
    'auth_middleware',
    'api_key_auth_middleware',
    'create_main_db_pool',
    'close_main_db_pool',
    'streaming_middleware'
]