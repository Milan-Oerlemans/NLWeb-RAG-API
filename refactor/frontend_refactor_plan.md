# Frontend Refactoring Plan for Single-Site Architecture

## 1. Introduction

This document outlines the plan to refactor the frontend of the NLWeb application to support a single-site architecture and use a new ticket-based authentication system for WebSocket connections. This will simplify the user interface, improve security, and prepare the frontend to be served from external websites like WordPress.

## 2. Analysis

The current frontend is designed to support multiple sites, with a UI that allows users to switch between them. The authentication for the WebSocket connection is handled by passing the user's auth token in the query parameters, which is not ideal for security. The new ticket-based system will provide a more secure way to authenticate WebSocket connections.

The goal of this refactoring is to:

*   Remove all multi-site UI and logic.
*   Implement the new ticket-based authentication flow for WebSocket connections.
*   Ensure a smooth user experience with proper failover mechanisms.
*   Allow users to chat without being logged in, while still providing the option to log in.

## 3. Plan

### 1. Implement Ticket-Based WebSocket Authentication

*   **File to Modify**: `static/chat-interface-unified.js`
*   **Modify `connectWebSocket()` method**:
    1.  Before creating the `WebSocket` object, make a `POST` request to `/api/auth/ws-ticket`.
    2.  The request must include the `X-API-Key` header. The API key will be passed in the `UnifiedChatInterface` constructor options (`this.options.apiKey`).
    3.  Handle the JSON response to extract the `ticket`.
    4.  Construct the new WebSocket URL using the ticket, e.g., `wss://<host>/chat/ws?ticket=<ticket>`.
    5.  Remove the old logic that appends `auth_token`, `user_id`, and other user info to the WebSocket URL's query string.
    6.  Add error handling for the ticket request.

### 2. Remove Multi-Site UI and Logic

*   **Files to Modify**:
    *   `static/chat-interface-unified.js`:
        1.  **Remove Site State**: Remove `this.state.sites` and simplify `this.state.selectedSite`. The concept of a site list and user-selectable site will be removed.
        2.  **Remove Site Loading**: Delete the `loadSitesNonBlocking()`, `loadSitesViaHttp()`, and `processSitesData()` methods.
        3.  **Update `createUserMessage()`**: Remove the `site: this.state.selectedSite` property from the message payload. The server will determine the site from the connection context.
        4.  **Remove Site Selector UI**: In the `showCenteredInput()` method, remove the HTML and associated event listeners for the site selector dropdown (`#site-selector-icon`, `#site-dropdown`).
        5.  **Remove "Asking..." text**: Remove any code that updates the `#chat-site-info` element, as this element will be removed.
    *   `static/conversation-manager.js`:
        1.  **Modify `updateConversationsList()`**: Remove the logic that groups conversations by site. The method should render a single, flat list of conversations, sorted by recency.
        2.  **Modify `loadLocalConversations()`**: Remove the `selectedSite` parameter and any logic that filters conversations by site. The sidebar should always show all conversations.
    *   `static/index.html`:
        1.  Remove the `#chat-site-info` element from the chat header, which displays "Asking [site]".
        2.  Hardcode the API key in the `UnifiedChatInterface` instantiation.
    *   `static/nlweb-dropdown-chat.js`:
        1.  **Update Instantiation**: This component initializes `UnifiedChatInterface`. The instantiation must be updated to pass the `apiKey` from its own configuration into the `UnifiedChatInterface` constructor. The component's configuration will now require an `apiKey` instead of a `site`.

### 3. Implement WebSocket Failover

*   **File to Modify**: `static/chat-interface-unified.js`
*   **Modify `handleDisconnection()` method**:
    1.  Implement a reconnection mechanism with exponential backoff.
    2.  Attempt to reconnect immediately on the first disconnection.
    3.  If the first attempt fails, wait for 2 seconds before the next attempt, then 4, 8, and 16 seconds.
    4.  If all 5 retries fail, display an error message to the user asking them to refresh the page.

### 4. Optional User Login

The user login functionality will be kept, but it will not be mandatory for chatting. Users can choose to log in if they want to, for example, to save their conversation history across devices (a future feature). The chat will be accessible to all users, whether they are logged in or not.

## 5. API_KEY Storage

For now, the API key will be hardcoded in the `static/index.html` file where the `UnifiedChatInterface` is instantiated. In a production environment, this should be replaced with a more secure method, such as fetching it from a configuration file or an environment variable.
