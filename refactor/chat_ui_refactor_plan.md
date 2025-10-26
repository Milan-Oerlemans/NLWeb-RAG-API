### Frontend Refactoring Plan

This plan outlines the steps to adapt the frontend to a single-site architecture and integrate the new ticket-based WebSocket authentication system.

#### 1. Implement Ticket-Based WebSocket Authentication

The primary change is to stop sending authentication tokens directly in the WebSocket URL and instead use a short-lived ticket obtained from the `/api/auth/ws-ticket` endpoint.

**File to Modify:** `static/chat-interface-unified.js`

-   **Modify `connectWebSocket()` method:**
    1.  Before creating the `WebSocket` object, make a `POST` request to `/api/auth/ws-ticket`.
    2.  The request must include the `X-API-Key` header. The API key will be passed in the `UnifiedChatInterface` constructor options (`this.options.apiKey`).
    3.  Handle the JSON response to extract the `ticket`.
    4.  Construct the new WebSocket URL using the ticket, e.g., `wss://<host>/chat/ws?ticket=<ticket>`.
    5.  Remove the old logic that appends `auth_token`, `user_id`, and other user info to the WebSocket URL's query string.
    6.  Add error handling for the ticket request.

#### 2. Remove Multi-Site UI and Logic

The frontend will no longer allow users to select or switch between different sites. The active site is implicitly defined by the API key used for authentication.

**Files to Modify:**

-   **`static/chat-interface-unified.js`:**
    1.  **Remove Site State:** Remove `this.state.sites` and simplify `this.state.selectedSite`. The concept of a site list and user-selectable site will be removed.
    2.  **Remove Site Loading:** Delete the `loadSitesNonBlocking()`, `loadSitesViaHttp()`, and `processSitesData()` methods.
    3.  **Update `createUserMessage()`:** Remove the `site: this.state.selectedSite` property from the message payload. The server will determine the site from the connection context.
    4.  **Remove Site Selector UI:** In the `showCenteredInput()` method, remove the HTML and associated event listeners for the site selector dropdown (`#site-selector-icon`, `#site-dropdown`).
    5.  **Remove "Asking..." text:** Remove any code that updates the `#chat-site-info` element, as this element will be removed.

-   **`static/conversation-manager.js`:**
    1.  **Modify `updateConversationsList()`:** Remove the logic that groups conversations by site. The method should render a single, flat list of conversations, sorted by recency.
    2.  **Modify `loadLocalConversations()`:** Remove the `selectedSite` parameter and any logic that filters conversations by site. The sidebar should always show all conversations.

-   **`static/index.html`:**
    1.  Remove the `#chat-site-info` element from the chat header, which displays "Asking [site]".

-   **`static/nlweb-dropdown-chat.js`:**
    1.  **Update Instantiation:** This component initializes `UnifiedChatInterface`. The instantiation must be updated to pass the `apiKey` from its own configuration into the `UnifiedChatInterface` constructor. The component's configuration will now require an `apiKey` instead of a `site`.