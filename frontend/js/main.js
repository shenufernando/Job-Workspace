// Main JavaScript file
const API_BASE_URL = 'http://localhost:5000/api';

// --- Auth & Utility Functions ---

function getAuthToken() {
    return localStorage.getItem('token');
}

function setAuthToken(token) {
    localStorage.setItem('token', token);
}

function removeAuthToken() {
    localStorage.removeItem('token');
}

function getCurrentUser() {
    return JSON.parse(localStorage.getItem('user') || '{}');
}

function setCurrentUser(user) {
    localStorage.setItem('user', JSON.stringify(user));
}

function removeCurrentUser() {
    localStorage.removeItem('user');
}

function isAuthenticated() {
    return !!getAuthToken();
}

function redirectIfNotAuthenticated() {
    if (!isAuthenticated()) {
        window.location.href = 'login.html';
    }
}

function redirectIfAuthenticated() {
    if (isAuthenticated()) {
        const user = getCurrentUser();
        if (user.role === 'admin') window.location.href = 'admin-dashboard.html';
        else if (user.role === 'provider') window.location.href = 'provider-dashboard.html';
        else if (user.role === 'worker') window.location.href = 'worker-dashboard.html';
    }
}

// --- API Request Function ---

async function apiRequest(endpoint, options = {}) {
    const token = getAuthToken();
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers
        });

        const contentType = response.headers.get('content-type');
        let data;

        if (contentType && contentType.includes('application/json')) {
            data = await response.json();
        } else {
            data = {};
        }

        if (!response.ok) {
            throw new Error(data.error || `Request failed with status ${response.status}`);
        }

        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// --- UI Helpers ---

function showAlert(message, type = 'info') {
    // Check if alert already exists to prevent stacking too many
    const existingAlert = document.querySelector('.alert-fixed');
    if (existingAlert) existingAlert.remove();

    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-fixed`;
    alertDiv.textContent = message;

    // Inline styles for floating alert
    alertDiv.style.position = 'fixed';
    alertDiv.style.top = '20px';
    alertDiv.style.right = '20px';
    alertDiv.style.padding = '15px 25px';
    alertDiv.style.borderRadius = '8px';
    alertDiv.style.color = 'white';
    alertDiv.style.zIndex = '5000'; // High z-index to show over modals
    alertDiv.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
    alertDiv.style.fontWeight = '500';
    alertDiv.style.animation = 'slideIn 0.3s ease-out';

    if (type === 'success') alertDiv.style.backgroundColor = '#10B981';
    else if (type === 'error') alertDiv.style.backgroundColor = '#EF4444';
    else alertDiv.style.backgroundColor = '#3B82F6';

    document.body.appendChild(alertDiv);

    setTimeout(() => {
        alertDiv.style.animation = 'fadeOut 0.3s ease-in';
        setTimeout(() => alertDiv.remove(), 300);
    }, 4000);
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-LK', {
        style: 'currency',
        currency: 'LKR'
    }).format(amount);
}

// --- CHAT SYSTEM LOGIC ---

let currentChatJobId = null;
let currentChatReceiverId = null;
let chatRefreshInterval = null;

async function openMessages(jobId, receiverId, receiverName) {
    currentChatJobId = jobId;
    currentChatReceiverId = receiverId;

    // 1. Inject Modal HTML if not present
    if (!document.getElementById('chatModal')) {
        const modalHtml = `
            <div id="chatModal" class="modal-overlay" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); z-index: 3000; justify-content: center; align-items: center; backdrop-filter: blur(5px);">
                <div class="modal-content" style="background: white; width: 95%; max-width: 500px; height: 600px; display: flex; flex-direction: column; border-radius: 12px; box-shadow: 0 25px 50px rgba(0,0,0,0.25); overflow: hidden;">
                    <div class="modal-header" style="background: #4F46E5; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; color: white;">
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <div style="width: 40px; height: 40px; background: rgba(255,255,255,0.2); border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                                <i class="fas fa-user" style="font-size: 1.2rem;"></i>
                            </div>
                            <div>
                                <h2 id="chatReceiverName" style="font-size: 1.1rem; margin: 0; font-weight: 600;">User</h2>
                                <small id="chatJobTitle" style="opacity: 0.9; font-size: 0.8rem;">Job Chat</small>
                            </div>
                        </div>
                        <button onclick="closeChatModal()" style="background: none; border: none; color: white; font-size: 2rem; cursor: pointer; line-height: 1;">&times;</button>
                    </div>
                    
                    <div id="chatMessages" style="flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 10px; background: #f3f4f6;">
                        <div style="text-align: center; margin-top: 50px; color: #9ca3af;">Loading messages...</div>
                    </div>

                    <form onsubmit="sendMessage(event)" style="padding: 15px; background: white; border-top: 1px solid #e5e7eb; display: flex; gap: 10px; align-items: center;">
                        <input type="text" id="messageInput" placeholder="Type a message..." autocomplete="off" required 
                            style="flex: 1; padding: 12px 15px; border: 1px solid #d1d5db; border-radius: 25px; outline: none; transition: border 0.2s;">
                        <button type="submit" style="background: #4F46E5; color: white; border: none; width: 45px; height: 45px; border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); transition: transform 0.1s;">
                            <i class="fas fa-paper-plane"></i>
                        </button>
                    </form>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHtml);
    }

    // 2. Update UI
    document.getElementById('chatReceiverName').textContent = receiverName;
    document.getElementById('chatJobTitle').textContent = `Job ID: ${jobId}`;

    // 3. Show Modal
    const modal = document.getElementById('chatModal');
    modal.style.display = 'flex';

    // Focus input
    setTimeout(() => document.getElementById('messageInput').focus(), 100);

    // 4. Load & Poll
    await loadMessages();
    if (chatRefreshInterval) clearInterval(chatRefreshInterval);
    chatRefreshInterval = setInterval(loadMessages, 3000);
}

async function loadMessages() {
    if (!currentChatJobId) return;

    try {
        const messages = await apiRequest(`/messages/job/${currentChatJobId}`);
        const chatBox = document.getElementById('chatMessages');
        const currentUser = getCurrentUser();

        chatBox.innerHTML = '';

        if (messages.length === 0) {
            chatBox.innerHTML = '<p style="text-align: center; color: #9ca3af; margin-top: 20px; font-size: 0.9rem;">No messages yet. Say hello!</p>';
            return;
        }

        messages.forEach(msg => {
            const isMe = msg.sender_id === currentUser.id; // Make sure backend sends 'id' in login response
            const bubble = document.createElement('div');

            // Dynamic styles for bubbles
            bubble.style.maxWidth = '75%';
            bubble.style.padding = '10px 15px';
            bubble.style.borderRadius = '18px';
            bubble.style.fontSize = '0.95rem';
            bubble.style.position = 'relative';
            bubble.style.wordWrap = 'break-word';
            bubble.style.marginBottom = '5px';
            bubble.style.lineHeight = '1.4';

            if (isMe) {
                bubble.style.alignSelf = 'flex-end';
                bubble.style.backgroundColor = '#4F46E5'; // Primary Color
                bubble.style.color = 'white';
                bubble.style.borderBottomRightRadius = '4px';
            } else {
                bubble.style.alignSelf = 'flex-start';
                bubble.style.backgroundColor = 'white';
                bubble.style.color = '#1f2937';
                bubble.style.borderBottomLeftRadius = '4px';
                bubble.style.boxShadow = '0 1px 2px rgba(0,0,0,0.05)';
                bubble.style.border = '1px solid #e5e7eb';
            }

            const time = new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

            bubble.innerHTML = `
                <div>${msg.message}</div>
                <div style="font-size: 0.7rem; text-align: right; margin-top: 4px; opacity: ${isMe ? '0.8' : '0.5'};">
                    ${time}
                </div>
            `;

            chatBox.appendChild(bubble);
        });

        chatBox.scrollTop = chatBox.scrollHeight;

    } catch (error) {
        console.error("Chat Error:", error);
    }
}

async function sendMessage(e) {
    e.preventDefault();
    const input = document.getElementById('messageInput');
    const text = input.value.trim();

    if (!text) return;

    try {
        // Optimistic UI: Clear input immediately
        input.value = '';

        await apiRequest('/messages', {
            method: 'POST',
            body: JSON.stringify({
                job_id: currentChatJobId,
                receiver_id: currentChatReceiverId,
                message: text
            })
        });

        loadMessages(); // Refresh to show sent message/timestamp from server

    } catch (error) {
        showAlert("Failed to send: " + error.message, 'error');
    }
}

function closeChatModal() {
    const modal = document.getElementById('chatModal');
    if (modal) modal.style.display = 'none';

    if (chatRefreshInterval) clearInterval(chatRefreshInterval);
    currentChatJobId = null;
    currentChatReceiverId = null;
}