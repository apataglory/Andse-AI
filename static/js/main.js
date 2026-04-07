/**
 * ANDSE AI - Global UI Controller
 * Manages UI States, Settings, and Utility Actions
 */

document.addEventListener("DOMContentLoaded", () => {
    const sidebar = document.querySelector('aside');
    const settingsBtn = document.getElementById('settings-btn');
    
    // --- 1. Sidebar Toggle (For Mobile/Small Screens) ---
    function toggleSidebar() {
        sidebar.classList.toggle('-translate-x-full');
    }

    // --- 2. Copy Code Functionality ---
    // Automatically adds "Copy" buttons to any code blocks the AI sends
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('copy-code-btn')) {
            const pre = e.target.closest('pre');
            const code = pre.querySelector('code').innerText;
            
            navigator.clipboard.writeText(code).then(() => {
                e.target.innerHTML = '<i class="fa-solid fa-check text-green-500"></i>';
                setTimeout(() => {
                    e.target.innerHTML = '<i class="fa-solid fa-copy"></i>';
                }, 2000);
            });
        }
    });

    // Mutation Observer to watch for new messages and add copy buttons
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            mutation.addedNodes.forEach((node) => {
                if (node.nodeType === 1) { // Element node
                    const preBlocks = node.querySelectorAll('pre');
                    preBlocks.forEach(pre => {
                        if (!pre.querySelector('.copy-code-btn')) {
                            const btn = document.createElement('button');
                            btn.className = 'copy-code-btn absolute top-3 right-3 text-gray-500 hover:text-white transition p-1';
                            btn.innerHTML = '<i class="fa-solid fa-copy"></i>';
                            pre.appendChild(btn);
                        }
                    });
                }
            });
        });
    });

    observer.observe(document.getElementById('chat-window'), { childList: true, subtree: true });

    // --- 3. Keyboard Shortcuts ---
    document.addEventListener('keydown', (e) => {
        // Ctrl + K to clear chat or search (Standard UX)
        if (e.ctrlKey && e.key === 'k') {
            e.preventDefault();
            document.getElementById('new-chat-btn').click();
        }
    });

    // --- 4. Settings Modal Trigger ---
    if (settingsBtn) {
        settingsBtn.addEventListener('click', () => {
            // This would trigger the settings.py logic built earlier
            console.log("Opening System Preferences...");
            // Implementation of a modal would go here
        });
    }

    console.log("ANDSE AI System Logic Initialized.");
});