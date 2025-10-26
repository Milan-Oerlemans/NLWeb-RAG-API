"""Authentication utilities for NLWeb."""

import logging
import os
import time
import uuid
from typing import Dict, Optional

import redis.asyncio as redis
from aiohttp import web
from psycopg_pool import AsyncConnectionPool

logger = logging.getLogger(__name__)

class WebSocketTicketStore:
    """
    Manages short-lived tickets for WebSocket authentication.
    Uses Redis if available (detecting LocalStack for local dev),
    otherwise falls back to an in-memory dict.
    """
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_client = None
        self.in_memory_store = {}

        # Determine Redis URL: explicit config > LocalStack > fallback
        final_redis_url = redis_url or os.getenv('REDIS_URL')
        if not final_redis_url:
            localstack_host = os.getenv('LOCALSTACK_HOSTNAME')
            if localstack_host:
                final_redis_url = f"redis://{localstack_host}:6379"
                logger.info(f"Detected LocalStack, attempting to use Redis at: {final_redis_url}")

        if final_redis_url:
            try:
                self.redis_client = redis.from_url(final_redis_url)
                logger.info(f"WebSocketTicketStore initialized with Redis at {final_redis_url}.")
            except Exception as e:
                logger.error(f"Failed to connect to Redis at {final_redis_url}: {e}. Falling back to in-memory store.")
                self.redis_client = None
        
        if not self.redis_client:
            logger.info("WebSocketTicketStore initialized with in-memory store as a fallback.")


    async def create_ticket(self, site_info: Dict, expires_in: int = 30) -> str:
        """Creates a new ticket and stores it."""
        ticket = str(uuid.uuid4())
        if self.redis_client:
            # The site_info dict is converted to a string for storage in Redis.
            await self.redis_client.setex(f"ws_ticket:{ticket}", expires_in, str(site_info))
        else:
            self.in_memory_store[ticket] = {
                "site_info": site_info,
                "expires_at": time.time() + expires_in,
            }
        return ticket

    async def consume_ticket(self, ticket: str) -> Optional[Dict]:
        """Validates a ticket and consumes it, returning the site info."""
        if self.redis_client:
            key = f"ws_ticket:{ticket}"
            # Use a transaction to get and delete atomically, preventing reuse.
            pipe = self.redis_client.pipeline()
            pipe.get(key)
            pipe.delete(key)
            results = await pipe.execute()
            site_info_str = results[0]
            if site_info_str:
                # eval() is used to safely convert the string representation of the dict back to a dict.
                # This is secure because we control the string that is being stored.
                return eval(site_info_str)
            return None
        else:
            ticket_data = self.in_memory_store.pop(ticket, None)
            if ticket_data and time.time() < ticket_data["expires_at"]:
                return ticket_data["site_info"]
            return None

async def authenticate_api_key(request: web.Request) -> Optional[Dict[str, any]]:
    """
    Authenticates a request using an API key from the X-API-Key header
    and returns site information.

    Args:
        request: The aiohttp web request.

    Returns:
        A dictionary containing site_id (UUID) and site (str) if successful,
        otherwise None.
    """
    api_key = request.headers.get('X-API-Key')

    if not api_key:
        return None

    pool = request.app.get('main_db_pool')
    if not pool:
        logger.error("Main DB pool not available for API key validation.")
        return None

    try:
        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT site_id FROM sites WHERE api_key = %s", (api_key,))
                result = await cur.fetchone()

                if result:
                    site_id_uuid = result[0]
                    return {
                        'site_id': site_id_uuid,
                        'site': str(site_id_uuid)
                    }
                else:
                    return None
    except Exception as e:
        logger.exception(f"Error during API key validation: {e}")
        return None
