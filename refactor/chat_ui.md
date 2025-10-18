# Chat UI Deep Dive

This document provides a detailed explanation of the NLWeb chat user interface, covering how files are served, how the UI handles different sites, the management of chat history, and the authentication flow.

## 1. File Serving

The chat UI is a client-side application built with vanilla JavaScript, HTML, and CSS. The files are served directly by the Python `aiohttp` web server.

-   **Server Entry Point**: `code/python/app-aiohttp.py` initializes and starts the `AioHTTPServer` from `webserver/aiohttp_server.py`.
-   **Static File Route**: The `AioHTTPServer` class sets up a route that serves the `static/` directory. Any request to a path that starts with `/static/` will serve the corresponding file from that directory. For example, accessing `http://localhost:8000/static/index.html` in the browser serves the main HTML file for the chat interface.
-   **Root Redirect**: The server is also configured to redirect the root URL (`/`) to `/static/index.html`, making it the default page.

The primary files for the chat interface are:
-   `static/index.html`: The main HTML structure.
-   `static/common-chat-styles.css` & `static/chat-page-styles.css`: The stylesheets for the UI.
-   `static/chat-interface-unified.js`: The core JavaScript module that drives the chat logic.
-   `static/conversation-manager.js`: Handles the management of chat history.
-   `static/oauth-login.js`: Manages the user authentication flow.

## 2. Site Differentiation

The UI needs to know which "site" to query. The concept of a "site" has evolved from a simple string name to a UUID (`site_id`) that is tied to an API key.

-   **Initial State**: The UI can be initialized with a `site` parameter from the URL query string (e.g., `?site=my-site-name`). This is handled in `static/index.html` and `static/chat-interface-unified.js`.
-   **Refactored Approach (Multi-Tenancy)**: The `refactor/site_id_propagation_plan.md` outlines the shift to a multi-tenant system where the site context is determined by an API key, not a URL parameter.
    -   In this new model, the UI (or the application hosting it, like `sitetor.ai`) would be configured with a specific API key.
    -   Every request to the backend `/ask` endpoint must include this API key in the `X-API-Key` header.
    -   The `api_key_auth_middleware` on the server (`code/python/webserver/middleware/api_auth.py`) intercepts the request, validates the API key against the `sites` table in the database, and retrieves the corresponding `site_id` (UUID).
    -   This `site_id` is then injected into the request context, ensuring that the RAG pipeline only operates on data for that specific site.
-   **UI Interaction**: The UI provides a dropdown to switch between sites. When a user selects a site, the `selectedSite` state in `UnifiedChatInterface` is updated. This value is then included in the `content` of the message sent to the backend. However, in the multi-tenant model, the server-side authentication middleware will override this with the `site_id` associated with the API key, making the client-side selection secondary.

## 3. Chat Memory and History

Chat history is managed entirely on the client-side, using the browser's **IndexedDB** for persistent storage. This allows conversations to be saved across browser sessions.

-   **`conversation-manager.js`**: This module is the core of the history management system.
    -   It uses the `indexed-storage.js` module (a wrapper around IndexedDB) to save and retrieve chat messages.
    -   When the application loads, `loadLocalConversations()` is called to fetch all stored messages from IndexedDB and reconstruct the conversation history.
    -   Messages are grouped by `conversation_id`.
-   **`chat-interface-unified.js`**:
    -   When a user sends a message, a `user` message object is created. This object includes the `conversation_id`, the query, the selected site, and a list of previous queries (`prev_queries`) for context.
    -   As the server streams back a response, each message chunk is received by `handleStreamData`.
    -   The `storeStreamingMessage` function adds each message to the current conversation object in memory.
    -   At the end of a streaming response (`endStreaming`), the `conversationManager.saveConversations()` method is called, which persists all new messages for the current conversation to IndexedDB.
-   **Contextual Memory**: For providing context to the LLM, the `createUserMessage` function in `chat-interface-unified.js` gathers the last 5 user messages from the current conversation's history and includes them in the `prev_queries` field of the message sent to the backend.

## 4. Authentication

User authentication is handled via OAuth 2.0, allowing users to log in with providers like Google, GitHub, etc. The authentication state is managed on the client-side, but validated on the server.

-   **`oauth-login.js`**: This module manages the entire frontend authentication flow.
    -   It fetches the available OAuth providers from the `/api/oauth/config` endpoint.
    -   When a user clicks a login button, it opens a popup window to the provider's authentication URL.
    -   After the user authenticates, the provider redirects to `/oauth/callback`, which then sends a message back to the main window containing the `access_token` and `user_info`.
    -   This information is then stored in the browser's `localStorage`.
-   **Site-Specificity**: Authentication itself is **not site-specific**. A user's identity (e.g., their Google account) is global across the entire NLWeb application. However, access control can be implemented on top of this. The current implementation focuses on identifying the user rather than restricting their access to specific sites.
-   **Authenticated Requests**:
    -   For features like saving/retrieving conversation history from a central database (a planned feature, as local storage is the current default), the `authToken` from `localStorage` would be sent in the `Authorization` header of API requests.
    -   The primary mechanism for site-specific data access remains the **API key (`X-API-Key`)**, which is separate from user authentication. The API key determines *what data* can be accessed (which site), while the user's OAuth login determines *who* is accessing it. This allows for scenarios where multiple authenticated users can interact with the same site, defined by a single API key.
