### Frontend Files and Capabilities Summary

This document provides an overview of the files in the `static` directory and their capabilities.

-   **`index.html`**: The main entry point for the full-page chat application. It sets up the HTML structure, including the sidebar for conversations and the main chat area. It initializes the `UnifiedChatInterface` for WebSocket connections and includes OAuth login functionality.

-   **`chat-interface-unified.js`**: This is the core of the chat application. The `UnifiedChatInterface` class manages the chat state, handles both WebSocket and SSE connections, sends and receives messages, and controls the overall UI.

-   **`conversation-manager.js`**: The `ConversationManager` class is responsible for managing the lifecycle of conversations. It handles loading, saving, and deleting conversations, primarily using IndexedDB for local storage. It also provides methods for updating the conversation list in the UI.

-   **`nlweb-dropdown-chat.js`**: Implements a self-contained, reusable dropdown chat component. The `NLWebDropdownChat` class creates a search input that, when used, opens a dropdown panel containing the chat interface. It initializes and wraps the `UnifiedChatInterface`.

-   **`chat-ui-common.js`**: A library of shared UI rendering methods. It includes functions for rendering search results, schema.org objects (like recipes), and other common message types into HTML.

-   **`oauth-login.js`**: Manages the entire OAuth authentication flow. It handles clicks on login buttons, opens the OAuth popup window, communicates with the backend to exchange authorization codes for tokens, and updates the UI to reflect the logged-in state.

-   **`indexed-storage.js`**: A wrapper for the browser's IndexedDB API. It provides a simple, promise-based interface for storing and retrieving chat messages and conversations, allowing for persistent client-side storage.

-   **`schemas.js`**: Defines the JavaScript class representations of the core data structures used in the application, such as `Message` and `Conversation`. This ensures a consistent data model between the client and server.

-   **Test & Example Pages**:
    -   `a2a_test.html`: A testing interface for the Agent-to-Agent (A2A) communication protocol.
    -   `mcp_test.html`: A testing interface for the Model Context Protocol (MCP), allowing for both standard and streaming requests.
    -   `dropdown-example.html`, `dropdown-simple-test.html`, `dropdown-test.html`: Various pages for demonstrating and testing the `nlweb-dropdown-chat.js` component.
    -   `debug.html`, `str_chat.html`, `nlwebsearch.html`, `nlws.html`, `small_orange.html`, `who.html`: Additional specialized test pages for different chat configurations and modes.

-   **Styling and Utility Files**:
    -   `*.css`: CSS files providing styles for the different chat interfaces and components.
    -   `*.js` (utility files like `utils.js`, `json-renderer.js`, etc.): Provide helper functions for tasks like HTML escaping, JSON rendering, and creating specific UI elements.
    -   `clear-storage.html`, `clearLocalStore.js`, `storage-manager.html`: Tools for developers to inspect and clear data from `localStorage` and `IndexedDB`.

-   **Modular Chat Components (`/chat` directory)**:
    -   `api-service.js`: A wrapper for making REST API calls to the backend.
    -   `chat-ui.js`: Manages the rendering of messages, typing indicators, and other core chat UI elements.
    -   `config-service.js`: Handles loading of frontend configuration, such as API endpoints and available sites.
    -   `event-bus.js`: A simple publish/subscribe module for communication between different components.
    -   `identity-service.js`: Manages user identity, including OAuth and anonymous users.
    -   `participant-tracker.js`: Tracks the state of participants in a conversation.
    -   `secure-renderer.js`: Provides methods for securely rendering HTML content to prevent XSS.
    -   `share-ui.js`: Manages the UI and logic for sharing conversations.
    -   `sidebar-ui.js`: Controls the rendering and behavior of the conversations sidebar.
    -   `site-selector-ui.js`: Manages the UI for selecting the data source/site for a query.
    -   `state-manager.js`: A centralized store for managing the application's state.
    -   `websocket-service.js`: A dedicated service for managing the WebSocket connection.
