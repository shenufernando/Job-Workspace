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

    if (options.body instanceof FormData) {
        delete headers['Content-Type'];
    }

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
        //    console.error('API Error:', error);
        throw error;
    }
}

// --- UI Helpers ---

function showAlert(message, type = 'info') {
    // Map legacy type names to SweetAlert2 icons
    const iconMap = { success: 'success', error: 'error', warning: 'warning', info: 'info' };
    const icon = iconMap[type] || 'info';

    if (type === 'success' || type === 'info') {
        // Non-blocking toast for positive feedback
        Swal.fire({
            toast: true,
            position: 'top-end',
            icon: icon,
            title: message,
            showConfirmButton: false,
            timer: 4000,
            timerProgressBar: true,
            customClass: { popup: 'swal-toast-custom' }
        });
    } else {
        // Centered modal for errors and warnings that need attention
        const titleMap = { error: 'Error', warning: 'Warning' };
        Swal.fire({
            title: titleMap[type] || 'Notice',
            text: message,
            icon: icon,
            confirmButtonColor: '#6366f1',
            confirmButtonText: 'OK',
            customClass: { popup: 'swal-modal-custom' }
        });
    }
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

let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let selectedImageFile = null;

async function openMessages(jobId, receiverId, receiverName) {
    currentChatJobId = jobId;
    currentChatReceiverId = receiverId;

    // 1. Inject Modal HTML if not present
    if (!document.getElementById('chatModal')) {
        const modalHtml = `
            <div id="chatModal" class="modal-overlay" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(15,23,42,0.45); z-index: 3000; justify-content: center; align-items: center; backdrop-filter: blur(6px);">
                <div class="modal-content" style="background: white; width: 95%; max-width: 500px; height: 600px; display: flex; flex-direction: column; border-radius: 20px; box-shadow: 0 24px 48px rgba(0,0,0,0.14); overflow: hidden;">
                    
                    <!-- Chat Header: clean white, dark text -->
                    <div style="background: #fff; padding: 14px 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e2e8f0; flex-shrink: 0;">
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <div style="width: 42px; height: 42px; background: #eff6ff; border: 2px solid #bfdbfe; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #2563eb;">
                                <i class="fas fa-user"></i>
                            </div>
                            <div>
                                <h2 id="chatReceiverName" style="font-size: 1rem; margin: 0; font-weight: 700; color: #0f172a;">User</h2>
                                <small id="chatJobTitle" style="color: #64748b; font-size: 0.78rem;">Job Chat</small>
                            </div>
                        </div>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <button onclick="startCall('audio')" style="background: #eff6ff; border: 1px solid #bfdbfe; color: #2563eb; width: 38px; height: 38px; border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: background 0.2s;" title="Audio Call">
                                <i class="fas fa-phone"></i>
                            </button>
                            <button onclick="startCall('video')" style="background: #eff6ff; border: 1px solid #bfdbfe; color: #2563eb; width: 38px; height: 38px; border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: background 0.2s;" title="Video Call">
                                <i class="fas fa-video"></i>
                            </button>
                            <button onclick="closeChatModal()" style="background: #f1f5f9; border: 1px solid #e2e8f0; color: #64748b; width: 34px; height: 34px; border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 1.1rem; line-height: 1;">&times;</button>
                        </div>
                    </div>
                    
                    <!-- Message area -->
                    <div id="chatMessages" style="flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 10px; background: #f8fafc;">
                        <div style="text-align: center; margin-top: 50px; color: #94a3b8; font-size: 0.9rem;">Loading messages...</div>
                    </div>

                    <!-- Input Area -->
                    <form id="chatForm" onsubmit="sendMessage(event)" style="padding: 12px 16px; background: white; border-top: 1px solid #e2e8f0; display: flex; gap: 10px; align-items: center; flex-shrink: 0;">
                        <button type="button" onclick="document.getElementById('imageUploadInput').click()" style="background: none; border: none; color: #94a3b8; font-size: 1.2rem; cursor: pointer; transition: color 0.2s; flex-shrink: 0;" title="Attach">
                            <i class="fas fa-paperclip"></i>
                        </button>
                        <input type="file" id="imageUploadInput" accept="image/*" style="display: none;" onchange="handleImageSelect(event)">
                        
                        <div id="imagePreviewContainer" style="display: none; position: relative; flex-shrink: 0;">
                            <img id="imagePreview" src="" style="height: 40px; border-radius: 6px; border: 1px solid #cbd5e1;">
                            <button type="button" onclick="clearSelectedImage()" style="position: absolute; top: -5px; right: -5px; background: #ef4444; color: white; border: none; border-radius: 50%; width: 16px; height: 16px; font-size: 10px; cursor: pointer; display: flex; align-items: center; justify-content: center;">&times;</button>
                        </div>

                        <input type="text" id="messageInput" placeholder="Type a message..." autocomplete="off" 
                            style="flex: 1; padding: 11px 18px; border: 1.5px solid #e2e8f0; border-radius: 999px; outline: none; font-family: inherit; font-size: 0.9rem; background: #f8fafc; color: #0f172a; transition: border-color 0.2s, box-shadow 0.2s;"
                            onfocus="this.style.borderColor='#2563eb'; this.style.boxShadow='0 0 0 3px rgba(37,99,235,.10)'; this.style.background='#fff';"
                            onblur="this.style.borderColor='#e2e8f0'; this.style.boxShadow=''; this.style.background='#f8fafc';">
                            
                        <button type="button" id="recordButton" onclick="toggleRecording()" style="background: none; border: none; color: #94a3b8; font-size: 1.1rem; cursor: pointer; flex-shrink: 0;" title="Voice message">
                            <i class="fas fa-microphone"></i>
                        </button>

                        <button type="submit" style="background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%); color: white; border: none; width: 42px; height: 42px; border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center; box-shadow: 0 3px 8px rgba(37,99,235,.30); transition: transform 0.15s, box-shadow 0.15s; flex-shrink: 0;">
                            <i class="fas fa-paper-plane" style="font-size: 0.92rem;"></i>
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
    if (!currentChatJobId || !currentChatReceiverId) return;

    try {
        const messages = await apiRequest(`/messages/job/${currentChatJobId}/${currentChatReceiverId}`);
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
                // Sent: Royal Blue, iMessage-style tail bottom-right
                bubble.style.alignSelf = 'flex-end';
                bubble.style.background = 'linear-gradient(135deg, #2563eb 0%, #3b82f6 100%)';
                bubble.style.color = 'white';
                bubble.style.borderRadius = '18px 18px 4px 18px';
                bubble.style.boxShadow = '0 2px 8px rgba(37,99,235,.28)';
            } else {
                // Received: canvas gray, tail bottom-left
                bubble.style.alignSelf = 'flex-start';
                bubble.style.backgroundColor = '#f1f5f9';
                bubble.style.color = '#0f172a';
                bubble.style.borderRadius = '18px 18px 18px 4px';
                bubble.style.border = '1px solid #e2e8f0';
            }

            const time = new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

            let contentHtml = '';
            if (msg.message_type === 'image') {
                contentHtml = `<img src="${API_BASE_URL.replace('/api', '')}/${msg.file_url}" style="max-width: 100%; border-radius: 8px; margin-bottom: 5px;">`;
                if (msg.message) contentHtml += `<div>${msg.message}</div>`;
            } else if (msg.message_type === 'audio') {
                contentHtml = `<audio controls src="${API_BASE_URL.replace('/api', '')}/${msg.file_url}"></audio>`;
            } else {
                contentHtml = `<div>${msg.message}</div>`;
            }

            bubble.innerHTML = `
                ${contentHtml}
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

function handleImageSelect(event) {
    const file = event.target.files[0];
    if (file) {
        selectedImageFile = file;
        const reader = new FileReader();
        reader.onload = function (e) {
            document.getElementById('imagePreview').src = e.target.result;
            document.getElementById('imagePreviewContainer').style.display = 'block';
            document.getElementById('messageInput').style.display = 'none';
        }
        reader.readAsDataURL(file);
    }
}

function clearSelectedImage() {
    selectedImageFile = null;
    document.getElementById('imageUploadInput').value = '';
    document.getElementById('imagePreviewContainer').style.display = 'none';
    document.getElementById('messageInput').style.display = 'block';
}

async function toggleRecording() {
    const recordBtn = document.getElementById('recordButton');

    if (!isRecording) {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);

            mediaRecorder.ondataavailable = e => {
                if (e.data && e.data.size > 0) {
                    audioChunks.push(e.data);
                }
            };

            mediaRecorder.onstop = async () => {
                mediaRecorder.stream.getTracks().forEach(track => track.stop());
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm;codecs=opus' });
                await sendMediaMessage(audioBlob, 'audio');
            };

            audioChunks = [];
            mediaRecorder.start(250);
            isRecording = true;
            recordBtn.style.color = '#ef4444';
            document.getElementById('messageInput').placeholder = "Recording... Click mic to send.";
            document.getElementById('messageInput').disabled = true;
        } catch (err) {
            showAlert("Microphone access denied or not available.", "error");
        }
    } else {
        mediaRecorder.stop();
        isRecording = false;
        recordBtn.style.color = '#6b7280';
        document.getElementById('messageInput').placeholder = "Type a message...";
        document.getElementById('messageInput').disabled = false;
    }
}

async function sendMediaMessage(blob, type) {
    try {
        const formData = new FormData();
        formData.append('job_id', currentChatJobId);
        formData.append('receiver_id', currentChatReceiverId);
        formData.append(type, blob, type === 'audio' ? 'voice_message.webm' : blob.name);

        await apiRequest('/messages', {
            method: 'POST',
            body: formData
        });
        loadMessages();
    } catch (error) {
        showAlert("Failed to send " + type + ": " + error.message, 'error');
    }
}

async function sendMessage(e) {
    e.preventDefault();

    if (selectedImageFile) {
        await sendMediaMessage(selectedImageFile, 'image');
        clearSelectedImage();
        return;
    }

    const input = document.getElementById('messageInput');
    const text = input.value.trim();

    if (!text) return;

    try {
        input.value = '';

        const formData = new FormData();
        formData.append('job_id', currentChatJobId);
        formData.append('receiver_id', currentChatReceiverId);
        formData.append('message', text);

        await apiRequest('/messages', {
            method: 'POST',
            body: formData
        });

        loadMessages();
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

// --- JITSI MEETS CALLING LOGIC ---
async function startCall(callType) {
    if (!currentChatJobId || !currentChatReceiverId) return;

    const currentUser = getCurrentUser();

    // Generate unique room name based on Job ID and User IDs
    const roomName = 'JobWorkspace_Job' + currentChatJobId + '_User' + Math.min(currentUser.id, currentChatReceiverId) + '_' + Math.max(currentUser.id, currentChatReceiverId);

    // Send automated text message notification
    let notificationText = callType === 'audio'
        ? `📞 ${currentUser.name} is requesting an Audio Call. Please click the 📞 (Phone) icon at the top to join.`
        : `📹 ${currentUser.name} is requesting a Video Call. Please click the 📹 (Video) icon at the top to join.`;

    try {
        const formData = new FormData();
        formData.append('job_id', currentChatJobId);
        formData.append('receiver_id', currentChatReceiverId);
        formData.append('message', notificationText);

        await apiRequest('/messages', {
            method: 'POST',
            body: formData
        });
        loadMessages();
    } catch (e) {
        console.error("Failed to send call notification:", e);
    }

    const iframeUrl = callType === 'audio' ? `https://meet.jit.si/${roomName}#config.startWithVideoMuted=true` : `https://meet.jit.si/${roomName}`;

    // Create and inject Call Modal Overlay
    if (!document.getElementById('jitsiCallModal')) {
        const modalHtml = `
            <div id="jitsiCallModal" class="modal-overlay" style="display: flex; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: #000; z-index: 4000; flex-direction: column;">
                <div style="background: #1f2937; padding: 15px; display: flex; justify-content: space-between; align-items: center; color: white;">
                    <h3 style="margin: 0; display: flex; align-items: center; gap: 10px;"><i class="fas fa-${callType === 'audio' ? 'phone' : 'video'}"></i> Active Call</h3>
                    <button onclick="endCall()" style="background: #ef4444; color: white; border: none; padding: 8px 16px; border-radius: 6px; font-weight: bold; cursor: pointer;">End Call</button>
                </div>
                <div style="flex: 1; width: 100%;">
                    <iframe src="${iframeUrl}" allow="camera; microphone; fullscreen; display-capture" style="width: 100%; height: 100%; border: none;"></iframe>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHtml);
    }
}

function endCall() {
    const callModal = document.getElementById('jitsiCallModal');
    if (callModal) {
        callModal.remove();
    }
}

async function inviteWorkerFromMatch(jobId, workerId, buttonElement) {
    if (!jobId || !workerId) return;

    buttonElement.disabled = true;
    const originalText = buttonElement.innerHTML;
    buttonElement.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Inviting...';

    try {
        await apiRequest(`/jobs/${jobId}/invite/${workerId}`, { method: 'POST' });

        buttonElement.innerHTML = '<i class="fas fa-check"></i> Requested';
        buttonElement.style.backgroundColor = '#10B981';
        buttonElement.style.color = '#ffffff';
        buttonElement.style.borderColor = '#10B981';
        buttonElement.classList.remove('btn-secondary');
    } catch (e) {
        buttonElement.disabled = false;
        buttonElement.innerHTML = originalText;
        showAlert(e.message, 'error');
    }
}

// --- Global Google Translate Cookie Fix ---
// Google sets the 'googtrans' cookie per directory level (e.g., /pages/). 
// This forces the translation cookie to the root '/' so the selected language persists globally.
document.addEventListener('DOMContentLoaded', () => {
    // Function to get a specific cookie
    const getCookie = (name) => {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    };

    // Function to set the cookie forcefully onto the root domain
    const setGlobalCookie = (name, value) => {
        document.cookie = `${name}=${value}; path=/; domain=${window.location.hostname};`;
    };

    // Periodically sync the googtrans cookie to the root path natively
    setInterval(() => {
        const transCookie = getCookie('googtrans');
        if (transCookie) {
            setGlobalCookie('googtrans', transCookie);
        }
    }, 1000);
});