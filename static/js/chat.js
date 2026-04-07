document.addEventListener("DOMContentLoaded", () => {
    // 1. Initialize Socket Connection
    const socket = io({ autoConnect: true });
    
    // 2. DOM Elements
    const chatWindow = document.getElementById('chat-window');
    const messageInput = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');
    const newChatBtn = document.getElementById('new-chat-btn');
    const sessionList = document.getElementById('session-list');
    const welcomeScreen = document.getElementById('welcome-screen');
    const chatTitle = document.getElementById('current-chat-title');

    // 3. State Management
    let currentSessionId = null;
    let currentAiMessageDiv = null;
    let rawAiContent = ""; // Stores raw markdown during streaming

    // ==========================================
    // 🔌 SOCKET EVENT HANDLERS
    // ==========================================

    socket.on('connect', () => {
        document.getElementById('connection-status').innerHTML = '<span class="w-2 h-2 rounded-full bg-green-500 mr-2 animate-pulse"></span> Online';
        loadSessions(); // Load history on connect
    });

    socket.on('disconnect', () => {
        document.getElementById('connection-status').innerHTML = '<span class="w-2 h-2 rounded-full bg-red-500 mr-2"></span> Offline';
    });

    // Handle incoming text chunks from the AI
    socket.on('message_chunk', (data) => {
        if (data.session_id !== currentSessionId) return;
        
        // Remove typing indicator if it exists
        const typingInd = document.getElementById('typing-indicator');
        if (typingInd) typingInd.remove();

        // Create new AI message bubble if it doesn't exist for this response
        if (!currentAiMessageDiv) {
            currentAiMessageDiv = createMessageBubble('ai');
            chatWindow.appendChild(currentAiMessageDiv);
            rawAiContent = "";
        }

        // Append chunk and parse Markdown to HTML
        rawAiContent += data.chunk;
        currentAiMessageDiv.querySelector('.message-content').innerHTML = marked.parse(rawAiContent);
        
        scrollToBottom();
    });

    socket.on('typing_start', () => {
        if (!document.getElementById('typing-indicator')) {
            const typingHtml = `
                <div id="typing-indicator" class="flex items-start max-w-3xl mx-auto w-full mb-6">
                    <div class="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center mr-4 flex-shrink-0"><i class="fa-solid fa-microchip text-white text-xs"></i></div>
                    <div class="bg-gray-900 rounded-2xl rounded-tl-none px-5 py-3 flex items-center space-x-1">
                        <span class="w-2 h-2 bg-gray-500 rounded-full"></span>
                        <span class="w-2 h-2 bg-gray-500 rounded-full"></span>
                        <span class="w-2 h-2 bg-gray-500 rounded-full"></span>
                    </div>
                </div>`;
            chatWindow.insertAdjacentHTML('beforeend', typingHtml);
            scrollToBottom();
        }
    });

    socket.on('typing_end', () => {
        currentAiMessageDiv = null; // Reset for next message
        const typingInd = document.getElementById('typing-indicator');
        if (typingInd) typingInd.remove();
    });

    socket.on('update_title', (data) => {
        if(data.session_id === currentSessionId) {
            chatTitle.innerText = data.title;
            loadSessions(); // Refresh sidebar
        }
    });

    // ==========================================
    // 💬 UI INTERACTION & LOGIC
    // ==========================================

    function createMessageBubble(sender, text = '') {
        const div = document.createElement('div');
        div.className = "flex items-start max-w-4xl mx-auto w-full mb-6 group";
        
        const isUser = sender === 'user';
        const avatarColor = isUser ? 'bg-gray-700' : 'bg-blue-600';
        const avatarIcon = isUser ? '<i class="fa-solid fa-user text-white text-xs"></i>' : '<i class="fa-solid fa-microchip text-white text-xs"></i>';
        const bubbleColor = isUser ? 'bg-gray-800' : 'bg-transparent text-gray-200';
        const rounded = isUser ? 'rounded-2xl rounded-tr-none' : ''; // AI is flat text, User is bubble

        // Parse markdown if initial text is provided
        const parsedText = text ? marked.parse(text) : '';

        div.innerHTML = `
            <div class="w-8 h-8 rounded-full ${avatarColor} flex items-center justify-center mr-4 flex-shrink-0 mt-1 shadow-sm">
                ${avatarIcon}
            </div>
            <div class="${bubbleColor} ${rounded} px-2 py-1 flex-1 overflow-hidden message-content prose prose-invert max-w-none">
                ${parsedText}
            </div>
        `;
        return div;
    }

    function sendMessage() {
        const text = messageInput.value.trim();
        if (!text) return;

        // Ensure we have a session
        if (!currentSessionId) {
            createNewSession().then(() => emitMessage(text));
        } else {
            emitMessage(text);
        }
    }

    function emitMessage(text) {
        // 1. Hide Welcome Screen
        if (welcomeScreen) welcomeScreen.style.display = 'none';

        // 2. Render User Message instantly
        const userMsg = createMessageBubble('user', text);
        chatWindow.appendChild(userMsg);
        
        // 3. Clear Input
        messageInput.value = '';
        messageInput.style.height = 'auto'; // Reset height
        scrollToBottom();

        // 4. Send via WebSocket
        socket.emit('send_message', {
            session_id: currentSessionId,
            message: text
        });
    }

    // ==========================================
    // 🗂️ SESSION MANAGEMENT (Sidebar)
    // ==========================================

    async function loadSessions() {
        try {
            const res = await fetch('/chat/sessions');
            const sessions = await res.json();
            
            sessionList.innerHTML = '';
            sessions.forEach(session => {
                const btn = document.createElement('button');
                btn.className = `w-full text-left px-3 py-2 rounded-lg text-sm truncate transition ${session.id === currentSessionId ? 'bg-gray-800 text-white' : 'text-gray-400 hover:bg-gray-800 hover:text-white'}`;
                btn.innerHTML = `<i class="fa-regular fa-message mr-2"></i> ${session.title}`;
                btn.onclick = () => loadSessionHistory(session.id, session.title);
                sessionList.appendChild(btn);
            });

            // If no active session, create one
            if (!currentSessionId && sessions.length === 0) {
                createNewSession();
            } else if (!currentSessionId && sessions.length > 0) {
                // Auto-load most recent
                loadSessionHistory(sessions[0].id, sessions[0].title);
            }
        } catch (e) { console.error("Failed to load sessions", e); }
    }

    async function createNewSession() {
        try {
            const res = await fetch('/chat/new', { method: 'POST' });
            const data = await res.json();
            currentSessionId = data.id;
            chatTitle.innerText = data.title;
            
            // Clear chat window
            chatWindow.innerHTML = '';
            if (welcomeScreen) chatWindow.appendChild(welcomeScreen);
            welcomeScreen.style.display = 'flex';
            
            socket.emit('join', { session_id: currentSessionId });
            loadSessions();
        } catch (e) { console.error("Failed to create session", e); }
    }

    async function loadSessionHistory(sessionId, title) {
        currentSessionId = sessionId;
        chatTitle.innerText = title;
        
        socket.emit('join', { session_id: currentSessionId });
        
        try {
            const res = await fetch(`/chat/session/${sessionId}`);
            const data = await res.json();
            
            chatWindow.innerHTML = ''; // Clear current
            
            if (data.messages.length === 0) {
                if (welcomeScreen) {
                    chatWindow.appendChild(welcomeScreen);
                    welcomeScreen.style.display = 'flex';
                }
            } else {
                data.messages.forEach(msg => {
                    chatWindow.appendChild(createMessageBubble(msg.sender, msg.content));
                });
                scrollToBottom();
            }
            loadSessions(); // Update active state in sidebar
        } catch (e) { console.error("Failed to load history", e); }
    }

    // ==========================================
    // 🛠️ UTILITIES
    // ==========================================

    function scrollToBottom() {
        chatWindow.scrollTo({ top: chatWindow.scrollHeight, behavior: 'smooth' });
    }

    // Auto-resize textarea
    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });

    // Enter to send (Shift+Enter for newline)
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Event Listeners
    sendBtn.addEventListener('click', sendMessage);
    newChatBtn.addEventListener('click', createNewSession);
});