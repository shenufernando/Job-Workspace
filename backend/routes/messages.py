from flask import Blueprint, request, jsonify
import sys
import os
import time
import uuid
from werkzeug.utils import secure_filename
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import get_db
from utils.auth import get_current_user

messages_bp = Blueprint('messages', __name__)

@messages_bp.route('/messages', methods=['POST'])
def send_message():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    if request.is_json:
        data = request.get_json()
        job_id = data.get('job_id')
        receiver_id = data.get('receiver_id')
        message = data.get('message', '')
    else:
        job_id = request.form.get('job_id')
        receiver_id = request.form.get('receiver_id')
        message = request.form.get('message', '')
    
    if not all([job_id, receiver_id]):
        return jsonify({'error': 'Job ID and receiver ID are required'}), 400

    # Handle file upload
    file_url = None
    message_type = 'text'
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads', 'messages')
    os.makedirs(upload_dir, exist_ok=True)

    if 'image' in request.files and request.files['image'].filename != '':
        file = request.files['image']
        filename = secure_filename(file.filename)
        unique_name = f"{int(time.time())}_{uuid.uuid4().hex[:8]}_{filename}"
        file_path = os.path.join(upload_dir, unique_name)
        file.save(file_path)
        file_url = f"uploads/messages/{unique_name}"
        message_type = 'image'
    
    elif 'audio' in request.files and request.files['audio'].filename != '':
        file = request.files['audio']
        filename = secure_filename(file.filename) or 'audio.webm'
        unique_name = f"{int(time.time())}_{uuid.uuid4().hex[:8]}_{filename}"
        file_path = os.path.join(upload_dir, unique_name)
        
        # Save completely without early truncation
        with open(file_path, "wb") as f:
            f.write(file.read())
            
        file_url = f"uploads/messages/{unique_name}"
        message_type = 'audio'
        
    if not message and message_type == 'text':
         return jsonify({'error': 'Message text is required if no file is uploaded'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Verify user has access to this job (either provider or accepted worker)
    cursor.execute("SELECT provider_id FROM job_posts WHERE id = %s", (job_id,))
    job = cursor.fetchone()
    
    if not job:
        cursor.close()
        return jsonify({'error': 'Job not found'}), 404
    
    # Check if user is provider or accepted worker
    if user['role'] == 'provider' and job[0] != user['user_id']:
        cursor.close()
        return jsonify({'error': 'Unauthorized'}), 403
    
    if user['role'] == 'worker':
        cursor.execute("""
            SELECT id FROM job_applications 
            WHERE job_id = %s AND worker_id = %s AND status = 'accepted'
        """, (job_id, user['user_id']))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Application must be accepted to message'}), 403
    
    # Create message
    cursor.execute("""
        INSERT INTO messages (job_id, sender_id, receiver_id, message, message_type, file_url)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (job_id, user['user_id'], receiver_id, message, message_type, file_url))
    
    # Create notification
    cursor.execute("""
        INSERT INTO notifications (user_id, type, title, message, related_id)
        VALUES (%s, 'new_message', 'New Message', 'You have received a new message.', %s)
    """, (receiver_id, job_id))
    
    conn.commit()
    cursor.close()
    
    return jsonify({'message': 'Message sent successfully'}), 201

@messages_bp.route('/messages/job/<int:job_id>', methods=['GET'])
def get_messages_legacy(job_id):
    # Fallback to prevent 500/CORS crashes for users with cached Javascript.
    return jsonify({'error': 'Please hard refresh your browser (Ctrl+Shift+R) or clear your cache to use the updated chat system.'}), 400

@messages_bp.route('/messages/job/<int:job_id>/<int:other_user_id>', methods=['GET'])
def get_messages(job_id, other_user_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Get all messages for this job between current user and other user
    cursor.execute("""
        SELECT m.*, 
               s.name as sender_name, 
               r.name as receiver_name
        FROM messages m
        JOIN users s ON m.sender_id = s.id
        JOIN users r ON m.receiver_id = r.id
        WHERE m.job_id = %s 
          AND ((m.sender_id = %s AND m.receiver_id = %s) 
               OR (m.sender_id = %s AND m.receiver_id = %s))
        ORDER BY m.created_at ASC
    """, (job_id, user['user_id'], other_user_id, other_user_id, user['user_id']))
    
    messages = cursor.fetchall()
    
    # Mark messages as read where current user is the receiver and other user is the sender
    cursor.execute("""
        UPDATE messages 
        SET is_read = TRUE 
        WHERE job_id = %s AND receiver_id = %s AND sender_id = %s AND is_read = FALSE
    """, (job_id, user['user_id'], other_user_id))
    
    conn.commit()
    cursor.close()
    
    return jsonify(messages), 200

@messages_bp.route('/messages/conversations', methods=['GET'])
def get_conversations():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Get all unique conversations
    cursor.execute("""
        SELECT DISTINCT j.id as job_id, j.title as job_title,
               CASE 
                   WHEN m.sender_id = %s THEN r.id
                   ELSE s.id
               END as other_user_id,
               CASE 
                   WHEN m.sender_id = %s THEN r.name
                   ELSE s.name
               END as other_user_name,
               (SELECT message FROM messages 
                WHERE job_id = j.id 
                ORDER BY created_at DESC LIMIT 1) as last_message,
               (SELECT created_at FROM messages 
                WHERE job_id = j.id 
                ORDER BY created_at DESC LIMIT 1) as last_message_time
        FROM messages m
        JOIN job_posts j ON m.job_id = j.id
        JOIN users s ON m.sender_id = s.id
        JOIN users r ON m.receiver_id = r.id
        WHERE m.sender_id = %s OR m.receiver_id = %s
        ORDER BY last_message_time DESC
    """, (user['user_id'], user['user_id'], user['user_id'], user['user_id']))
    
    conversations = cursor.fetchall()
    cursor.close()
    
    return jsonify(conversations), 200

