"""API Key Authentication Middleware"""

import os
import logging
from aiohttp import web
from psycopg_pool import AsyncConnectionPool

logger = logging.getLogger(__name__)

# Public endpoints that don't require API key authentication
PUBLIC_ENDPOINTS = {
    '/health',
    '/ready',
    '/oauth/callback',
    '/api/oauth/config',
    '/who',
    '/sites',
    '/config',
    '/chat'
}

async def create_main_db_pool(app: web.Application):
    """Create and attach the main database connection pool to the app."""
    try:
        conn_info = (
            f"host={os.getenv('MAIN_DB_HOST')} "
            f"dbname={os.getenv('MAIN_DB_NAME')} "
            f"user={os.getenv('MAIN_DB_USER')} "
            f"password={os.getenv('MAIN_DB_PASSWORD')}"
        )
        logger.info(f"Creating main DB pool with conn info: {conn_info}")
        pool = AsyncConnectionPool(conninfo=conn_info, min_size=1, max_size=10)
        app['main_db_pool'] = pool
        
        logger.info("Main application database connection pool created.")
    except Exception as e:
        logger.exception(f"Failed to create main database connection pool: {e}")
        # It's better to raise an error here to prevent the app from starting
        # in a broken state, but for now, we'll log and continue.
        app['main_db_pool'] = None


async def close_main_db_pool(app: web.Application):
    """Close the main database connection pool."""
    pool = app.get('main_db_pool')
    if pool:
        await pool.close()
        logger.info("Main application database connection pool closed.")


from webserver.middleware.auth_utils import authenticate_api_key

@web.middleware
async def api_key_auth_middleware(request: web.Request, handler):
    """
    Authenticate requests using an API key.
    """
    path = request.path

    # Public endpoints do not require API key authentication.
    public_endpoints_tuple = tuple(PUBLIC_ENDPOINTS)
    if path in PUBLIC_ENDPOINTS or path.startswith('/static/') or path.startswith('/html/') or path == '/favicon.ico' or path.startswith(public_endpoints_tuple) or path == '/':
        return await handler(request)

    # WebSocket connections are authenticated via a ticket in the websocket_handler.
    if path.startswith('/chat/ws/'):
        return await handler(request)

    # The new ticket endpoint is authenticated within its own handler.
    if path == '/api/auth/ws-ticket':
        return await handler(request)

    site_info = await authenticate_api_key(request)
    if site_info:
        request['site_id'] = site_info['site_id']
        request['site'] = site_info['site']
        return await handler(request)
    
    return web.json_response({'error': 'Invalid or Missing API key'}, status=401)
