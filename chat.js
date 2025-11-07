class SQLAgentChat {
    constructor() {
        this.messages = [];
        this.currentThreadId = null;
        this.threads = {};
        this.isTyping = false;
        this.uploadedFile = null;
        this.threadToDelete = null;
        
        this.initElements();
        this.bindEvents();
        this.loadThreads();
    }
    
    initElements() {
        this.sidebar = document.getElementById('sidebar');
        this.sidebarToggle = document.getElementById('sidebarToggle');
        this.newChatBtn = document.getElementById('newChatBtn');
        this.threadList = document.getElementById('threadList');
        this.messagesContainer = document.getElementById('messagesContainer');
        this.messagesScroll = document.getElementById('messagesScroll');
        this.messageInput = document.getElementById('messageInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.fileInput = document.getElementById('fileInput');
        this.fileUploadBtn = document.getElementById('fileUploadBtn');
        this.deleteModal = document.getElementById('deleteModal');
        this.confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
        this.cancelDeleteBtn = document.getElementById('cancelDeleteBtn');
    }
    
    bindEvents() {
        this.sidebarToggle.addEventListener('click', () => {
            this.sidebar.classList.toggle('collapsed');
        });
        
        this.newChatBtn.addEventListener('click', () => {
            this.createNewThread();
        });
        
        this.messageInput.addEventListener('input', () => {
            this.handleInputChange();
            this.autoResize();
        });
        
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        this.sendBtn.addEventListener('click', () => {
            this.sendMessage();
        });
        
        this.fileUploadBtn.addEventListener('click', () => {
            this.fileInput.click();
        });
        
        this.fileInput.addEventListener('change', (e) => {
            this.handleFileUpload(e);
        });
        
        this.confirmDeleteBtn.addEventListener('click', () => {
            this.confirmDelete();
        });
        
        this.cancelDeleteBtn.addEventListener('click', () => {
            this.closeDeleteModal();
        });
        
        this.deleteModal.addEventListener('click', (e) => {
            if (e.target === this.deleteModal) {
                this.closeDeleteModal();
            }
        });
    }
    
    autoResize() {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';
    }
    
    handleInputChange() {
        const hasText = this.messageInput.value.trim().length > 0;
        const hasFile = this.uploadedFile !== null;
        this.sendBtn.disabled = !hasText || this.isTyping;
    }
    
    handleFileUpload(event) {
        const file = event.target.files[0];
        
        if (!file) {
            this.clearFileUpload();
            return;
        }
        
        // Validate file extension
        const fileName = file.name.toLowerCase();
        if (!fileName.endsWith('.db')) {
            alert('Please select a valid SQLite database file (.db)');
            this.clearFileUpload();
            return;
        }
        
        // Validate file size (limit to 50MB)
        const maxSize = 50 * 1024 * 1024; // 50MB in bytes
        if (file.size > maxSize) {
            alert('File size must be less than 50MB');
            this.clearFileUpload();
            return;
        }
        
        // File is valid
        this.uploadedFile = file;
        this.fileUploadBtn.classList.add('uploaded');
        this.fileUploadBtn.title = `Database loaded: ${file.name}`;
        this.handleInputChange();
    }
    
    clearFileUpload() {
        this.uploadedFile = null;
        this.fileInput.value = '';
        this.fileUploadBtn.classList.remove('uploaded');
        this.fileUploadBtn.title = 'Upload SQLite database file';
        this.handleInputChange();
    }
    
    createNewThread() {
        const threadId = 'thread_' + Date.now();
        this.threads[threadId] = {
            id: threadId,
            title: 'New Chat',
            messages: [],
            createdAt: new Date()
        };
        
        this.switchToThread(threadId);
        this.renderThreadList();
        this.saveState(); // Save immediately
        this.messageInput.focus();
    }
    
    switchToThread(threadId) {
        this.currentThreadId = threadId;
        this.messages = this.threads[threadId].messages;
        this.renderMessages();
        this.updateActiveThread();
        this.saveState(); // Save current thread change
    }
    
    deleteThread(threadId) {
        this.threadToDelete = threadId;
        this.openDeleteModal();
    }
    
    openDeleteModal() {
        this.deleteModal.classList.add('active');
    }
    
    closeDeleteModal() {
        this.deleteModal.classList.remove('active');
        this.threadToDelete = null;
    }
    
    confirmDelete() {
        if (this.threadToDelete) {
            delete this.threads[this.threadToDelete];
            
            // If deleting current thread, switch to another or create new
            if (this.currentThreadId === this.threadToDelete) {
                const remainingThreads = Object.keys(this.threads);
                if (remainingThreads.length > 0) {
                    this.switchToThread(remainingThreads[0]);
                } else {
                    this.createNewThread();
                }
            }
            
            this.renderThreadList();
            this.saveState(); // Save immediately after deletion
        }
        
        this.closeDeleteModal();
    }
    
    updateActiveThread() {
        document.querySelectorAll('.thread-item').forEach(item => {
            item.classList.remove('active');
        });
        
        const activeItem = document.querySelector(`[data-thread-id="${this.currentThreadId}"]`);
        if (activeItem) {
            activeItem.classList.add('active');
        }
    }
    
    renderThreadList() {
        const threadEntries = Object.values(this.threads)
            .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
            
        this.threadList.innerHTML = threadEntries.map(thread => {
            const lastMessage = thread.messages[thread.messages.length - 1];
            const preview = lastMessage ? 
                (lastMessage.content.length > 50 ? 
                    lastMessage.content.substring(0, 50) + '...' : 
                    lastMessage.content) : 
                'No messages yet';
                
            return `
                <div class="thread-item" data-thread-id="${thread.id}">
                    <div class="thread-content">
                        <div class="thread-title">${thread.title}</div>
                        <div class="thread-preview">${preview}</div>
                    </div>
                    <button class="delete-thread-btn" data-thread-id="${thread.id}" title="Delete chat">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                            <path d="M3 6h18"/>
                            <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/>
                            <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
                        </svg>
                    </button>
                </div>
            `;
        }).join('');
        
        // Add click handlers
        document.querySelectorAll('.thread-item').forEach(item => {
            item.addEventListener('click', (e) => {
                // Prevent switching if clicking delete button
                if (e.target.closest('.delete-thread-btn')) return;
                const threadId = item.dataset.threadId;
                this.switchToThread(threadId);
            });
        });
        
        // Add delete handlers
        document.querySelectorAll('.delete-thread-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const threadId = btn.dataset.threadId;
                this.deleteThread(threadId);
            });
        });
    }
    
    async sendMessage() {
        const content = this.messageInput.value.trim();
        if (!content || this.isTyping) return;
        
        // Create thread if none exists
        if (!this.currentThreadId) {
            this.createNewThread();
        }
        
        // Add user message
        const userMessage = {
            id: 'msg_' + Date.now(),
            role: 'user',
            content: content,
            timestamp: new Date()
        };
        
        this.messages.push(userMessage);
        this.threads[this.currentThreadId].messages = this.messages;
        this.saveState(); // Save immediately after adding user message
        
        // Update thread title if it's the first message
        if (this.messages.length === 1) {
            this.threads[this.currentThreadId].title = content.length > 30 ? 
                content.substring(0, 30) + '...' : content;
            this.renderThreadList();
        }
        
        // Clear input
        this.messageInput.value = '';
        this.handleInputChange();
        this.autoResize();
        
        // Clear uploaded file after sending
        this.clearFileUpload();
        
        // Render messages
        this.renderMessages();
        this.scrollToBottom();
        
        // Show typing indicator
        this.showTypingIndicator();
        
        // Send to SQL Agent API (replace with your actual API endpoint)
        try {
            const response = await this.callSQLAgentAPI(content, this.uploadedFile);
            this.hideTypingIndicator();
            
            // Add assistant response
            const assistantMessage = {
                id: 'msg_' + Date.now(),
                role: 'assistant',
                content: response,
                timestamp: new Date()
            };
            
            this.messages.push(assistantMessage);
            this.threads[this.currentThreadId].messages = this.messages;
            this.saveState(); // Save immediately after adding assistant message
            this.renderMessages();
            this.scrollToBottom();
            
        } catch (error) {
            this.hideTypingIndicator();
            console.error('Error calling SQL Agent API:', error);
            
            // Show error message
            const errorMessage = {
                id: 'msg_' + Date.now(),
                role: 'assistant',
                content: 'Sorry, I encountered an error processing your request. Please try again.',
                timestamp: new Date()
            };
            
            this.messages.push(errorMessage);
            this.threads[this.currentThreadId].messages = this.messages;
            this.saveState(); // Save immediately after adding error message
            this.renderMessages();
            this.scrollToBottom();
        }
    }
    
    async callSQLAgentAPI(query, file = null) {
        // Replace this with your actual SQL Agent API endpoint
        const formData = new FormData();
        formData.append('query', query);
        
        if (file) {
            formData.append('database', file);
            console.log(`Sending query with database file: ${file.name} (${file.size} bytes)`);
        }
        
        const response = await fetch('/api/sql-agent', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('API request failed');
        }
        
        const data = await response.json();
        return data.response || 'No response received';
    }
    
    showTypingIndicator() {
        this.isTyping = true;
        this.handleInputChange();
        
        const typingHtml = `
            <div class="typing-indicator" id="typingIndicator">
                <div class="message-avatar">AI</div>
                <div>
                    <span>SQL Agent is thinking</span>
                    <div class="typing-dots">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                </div>
            </div>
        `;
        
        this.messagesScroll.insertAdjacentHTML('beforeend', typingHtml);
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        this.isTyping = false;
        this.handleInputChange();
        
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    renderMessages() {
        this.messagesScroll.innerHTML = this.messages.map(message => {
            const time = message.timestamp.toLocaleTimeString([], { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
            
            return `
                <div class="message ${message.role}">
                    <div class="message-avatar">
                        ${message.role === 'user' ? 'You' : 'AI'}
                    </div>
                    <div class="message-content">
                        <div class="message-bubble">
                            ${this.formatMessageContent(message.content)}
                        </div>
                        <div class="message-time">${time}</div>
                    </div>
                </div>
            `;
        }).join('');
    }
    
    formatMessageContent(content) {
        // Use marked to parse full markdown
        return marked.parse(content);
    }
    
    scrollToBottom() {
        setTimeout(() => {
            this.messagesScroll.scrollTop = this.messagesScroll.scrollHeight;
        }, 100);
    }
    
    loadThreads() {
        try {
            // Load from localStorage or create initial thread
            const savedState = localStorage.getItem('sqlagent_chat_state');
            if (savedState) {
                const state = JSON.parse(savedState);
                this.threads = state.threads || {};
                this.currentThreadId = state.currentThreadId || null;
                
                // Convert date strings back to Date objects
                Object.values(this.threads).forEach(thread => {
                    if (thread.createdAt) {
                        thread.createdAt = new Date(thread.createdAt);
                    }
                    if (thread.messages) {
                        thread.messages.forEach(message => {
                            if (message.timestamp) {
                                message.timestamp = new Date(message.timestamp);
                            }
                        });
                    }
                });
                
                const threadIds = Object.keys(this.threads);
                if (threadIds.length > 0) {
                    // If we have a saved currentThreadId and it exists, use it
                    if (this.currentThreadId && this.threads[this.currentThreadId]) {
                        this.switchToThread(this.currentThreadId);
                    } else {
                        // Otherwise use the first thread
                        this.switchToThread(threadIds[0]);
                    }
                    this.renderThreadList();
                    return;
                }
            }
        } catch (error) {
            console.warn('Failed to load chat state from localStorage:', error);
            // Clear corrupted data
            localStorage.removeItem('sqlagent_chat_state');
        }
        
        // Create initial thread if none exist or loading failed
        this.createNewThread();
    }
    
    saveState() {
        try {
            const state = {
                threads: this.threads,
                currentThreadId: this.currentThreadId
            };
            localStorage.setItem('sqlagent_chat_state', JSON.stringify(state));
        } catch (error) {
            console.warn('Failed to save chat state to localStorage:', error);
        }
    }
    
    // Auto-save state periodically
    startAutoSave() {
        setInterval(() => {
            this.saveState();
        }, 5000); // Save every 5 seconds
    }
}

// Initialize chat when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const chat = new SQLAgentChat();
    chat.startAutoSave();
});