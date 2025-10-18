"""API Key Authentication Middleware"""

import os
import logging
from aiohttp import web
from psycopg_pool import AsyncConnectionPool

logger = logging.getLogger(__name__)

# Public endpoints that don't require API key authentication
PUBLIC_ENDPOINTS = {
    '/',
    '/health',
    '/ready',
    '/oauth/callback',
    '/api/oauth/config',
    '/who',
    '/sites',
    '/config',
    '/chat',
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


@web.middleware
async def api_key_auth_middleware(request: web.Request, handler):
    """
    Authenticate requests using an API key.
    """

    path = request.path

    is_public = (
        path in PUBLIC_ENDPOINTS or
        path.startswith('/static/') or
        path.startswith('/html/') or
        path == '/favicon.ico'
    )


    if path.startswith('/chat/ws/'):
        # For WebSocket upgrade requests, we'll let them through to the handler
        # which will check auth separately since WebSocket can't use standard HTTP auth
        return await handler(request)
    public_endpoints_tuple = tuple(PUBLIC_ENDPOINTS)

    if path.startswith(public_endpoints_tuple):
        # Public endpoint, no auth required
        return await handler(request)

    api_key = request.headers.get('X-API-Key')

    if not api_key:
        return web.json_response({'error': 'API key is missing'}, status=401)


    pool = request.app.get('main_db_pool')
    if not pool:
        logger.error("Main DB pool not available for API key validation.")
        return web.json_response({'error': 'Internal server error'}, status=500)

    try:
        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT site_id FROM sites WHERE api_key = %s", (api_key,))
                result = await cur.fetchone()

                if result:
                    site_id_uuid = result[0]
                    # Attach site_id (UUID) and site (string) to the request
                    request['site_id'] = site_id_uuid
                    request['site'] = str(site_id_uuid)
                    return await handler(request)
                else:
                    return web.json_response({'error': 'Invalid API key'}, status=401)
    except Exception as e:
        logger.exception(f"Error during API key validation: {e}")
        return web.json_response({'error': 'Internal server error'}, status=500)