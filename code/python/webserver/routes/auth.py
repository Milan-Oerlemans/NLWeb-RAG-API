"""Authentication-related API routes."""

import logging
from aiohttp import web
from webserver.middleware.auth_utils import authenticate_api_key, WebSocketTicketStore

logger = logging.getLogger(__name__)

def setup_auth_routes(app: web.Application):
    """Setup authentication-related API routes."""
    app.router.add_post('/api/auth/ws-ticket', create_ws_ticket_handler)

async def create_ws_ticket_handler(request: web.Request) -> web.Response:
    """
    Handles the creation of a short-lived ticket for WebSocket authentication.
    Authenticates the request using the X-API-Key header.
    """
    site_info = await authenticate_api_key(request)
    if not site_info:
        return web.json_response({'error': 'Invalid API key'}, status=401)

    ticket_store: WebSocketTicketStore = request.app['ws_ticket_store']
    ticket = await ticket_store.create_ticket(site_info)

    return web.json_response({'ticket': ticket})
