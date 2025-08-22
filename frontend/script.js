// Chat Application Frontend
class ChatApp {
    constructor() {
        this.apiBase = 'http://localhost:8000';
        this.websocket = null;
        this.currentUser = null;
        this.currentRoom = null;
        this.token = localStorage.getItem('chat_token');
        
        this.initializeEventListeners();
        this.checkAuthStatus();
    }
    
    initializeEventListeners() {
        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });
        
        // Form submissions
        document.getElementById('loginForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.login();
        });
        
        document.getElementById('registerForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.register();
        });
        
        // Chat controls
        document.getElementById('logout-btn').addEventListener('click', () => {
            this.logout();
        });
        
        document.getElementById('create-room-btn').addEventListener('click', () => {
            this.createRoom();
        });
        
        document.getElementById('room-selector').addEventListener('change', (e) => {
            this.joinRoom(e.target.value);
        });
        
        document.getElementById('send-btn').addEventListener('click', () => {
            this.sendMessage();
        });
        
        document.getElementById('message-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
    }
    
    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });
        
        // Update forms
        document.querySelectorAll('.auth-form').forEach(form => {
            form.classList.toggle('active', form.id === `${tabName}-form`);
        });
    }
    
    async login() {
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;
        
        try {
            this.showLoading(true);
            
            const response = await fetch(`${this.apiBase}/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password }),
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.token = data.access_token;
                this.currentUser = {
                    id: data.user_id,
                    email: data.email
                };
                
                localStorage.setItem('chat_token', this.token);
                this.showToast('Login successful!', 'success');
                this.showChatSection();
            } else {
                this.showToast(data.detail || 'Login failed', 'error');
            }
        } catch (error) {
            this.showToast('Network error. Please try again.', 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    async register() {
        const username = document.getElementById('register-username').value;
        const email = document.getElementById('register-email').value;
        const password = document.getElementById('register-password').value;
        
        try {
            this.showLoading(true);
            
            const response = await fetch(`${this.apiBase}/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, email, password }),
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showToast('Registration successful! Please login.', 'success');
                this.switchTab('login');
                // Clear register form
                document.getElementById('registerForm').reset();
            } else {
                this.showToast(data.detail || 'Registration failed', 'error');
            }
        } catch (error) {
            this.showToast('Network error. Please try again.', 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    async createRoom() {
        const roomName = document.getElementById('room-name').value.trim();
        
        if (!roomName) {
            this.showToast('Please enter a room name', 'error');
            return;
        }
        
        try {
            this.showLoading(true);
            
            const response = await fetch(`${this.apiBase}/chat-rooms`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.token}`,
                },
                body: JSON.stringify({ 
                    name: roomName,
                    description: `Chat room: ${roomName}`,
                    is_private: false
                }),
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showToast('Room created successfully!', 'success');
                document.getElementById('room-name').value = '';
                this.joinRoom(data.room_id);
            } else {
                this.showToast(data.detail || 'Failed to create room', 'error');
            }
        } catch (error) {
            this.showToast('Network error. Please try again.', 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    async joinRoom(roomId) {
        if (!roomId) return;
        
        this.currentRoom = roomId;
        
        // Close existing WebSocket connection
        if (this.websocket) {
            this.websocket.close();
        }
        
        // Connect to WebSocket
        this.connectWebSocket(roomId);
        
        // Load existing messages
        await this.loadMessages(roomId);
        
        // Enable message input
        document.getElementById('message-input').disabled = false;
        document.getElementById('send-btn').disabled = false;
        
        // Update room selector
        document.getElementById('room-selector').value = roomId;
    }
    
    async loadMessages(roomId) {
        try {
            const response = await fetch(`${this.apiBase}/chat-rooms/${roomId}/messages`, {
                headers: {
                    'Authorization': `Bearer ${this.token}`,
                },
            });
            
            if (response.ok) {
                const messages = await response.json();
                this.displayMessages(messages.reverse()); // Show oldest first
            }
        } catch (error) {
            console.error('Failed to load messages:', error);
        }
    }
    
    connectWebSocket(roomId) {
        const wsUrl = `ws://localhost:8000/ws/${roomId}?token=${this.token}`;
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onopen = () => {
            console.log('WebSocket connected');
        };
        
        this.websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };
        
        this.websocket.onclose = () => {
            console.log('WebSocket disconnected');
        };
        
        this.websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.showToast('Connection error', 'error');
        };
    }
    
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'message':
                this.addMessage(data, data.user_id === this.currentUser.id);
                break;
            case 'user_joined':
                this.addSystemMessage(`${data.username} joined the chat`);
                break;
            case 'user_left':
                this.addSystemMessage(`${data.username} left the chat`);
                break;
            case 'system':
                this.addSystemMessage(data.content);
                break;
        }
    }
    
    sendMessage() {
        const input = document.getElementById('message-input');
        const message = input.value.trim();
        
        if (!message || !this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
            return;
        }
        
        this.websocket.send(JSON.stringify({
            content: message,
            type: 'message'
        }));
        
        input.value = '';
    }
    
    addMessage(data, isOwn = false) {
        const messagesContainer = document.getElementById('messages-container');
        
        // Remove welcome message if it exists
        const welcomeMessage = messagesContainer.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isOwn ? 'own' : 'other'}`;
        
        const timestamp = new Date(data.timestamp).toLocaleTimeString();
        
        messageDiv.innerHTML = `
            <div class="message-header">
                <span>${data.username}</span>
                <span>${timestamp}</span>
            </div>
            <div class="message-content">${this.escapeHtml(data.content)}</div>
        `;
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    addSystemMessage(content) {
        const messagesContainer = document.getElementById('messages-container');
        
        // Remove welcome message if it exists
        const welcomeMessage = messagesContainer.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message system';
        messageDiv.innerHTML = `
            <div class="message-content">${this.escapeHtml(content)}</div>
        `;
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    displayMessages(messages) {
        const messagesContainer = document.getElementById('messages-container');
        messagesContainer.innerHTML = '';
        
        messages.forEach(message => {
            this.addMessage({
                content: message.content,
                username: message.username,
                timestamp: message.created_at,
                user_id: message.user_id
            }, message.user_id === this.currentUser.id);
        });
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    checkAuthStatus() {
        if (this.token) {
            this.getCurrentUser();
        }
    }
    
    async getCurrentUser() {
        try {
            const response = await fetch(`${this.apiBase}/users/me`, {
                headers: {
                    'Authorization': `Bearer ${this.token}`,
                },
            });
            
            if (response.ok) {
                const userData = await response.json();
                this.currentUser = userData;
                this.showChatSection();
            } else {
                this.logout();
            }
        } catch (error) {
            this.logout();
        }
    }
    
    showChatSection() {
        document.getElementById('auth-section').classList.add('hidden');
        document.getElementById('chat-section').classList.remove('hidden');
        document.getElementById('current-user').textContent = this.currentUser.username;
    }
    
    logout() {
        this.token = null;
        this.currentUser = null;
        this.currentRoom = null;
        
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
        
        localStorage.removeItem('chat_token');
        
        document.getElementById('chat-section').classList.add('hidden');
        document.getElementById('auth-section').classList.remove('hidden');
        
        // Clear forms
        document.getElementById('loginForm').reset();
        document.getElementById('registerForm').reset();
        
        this.showToast('Logged out successfully', 'success');
    }
    
    showLoading(show) {
        document.getElementById('loading').classList.toggle('hidden', !show);
    }
    
    showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        
        toastContainer.appendChild(toast);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
}

// Initialize the app when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
});