from flask import Blueprint, request, jsonify
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import get_db
from utils.auth import get_current_user, role_required

users_bp = Blueprint('users', __name__)

@users_bp.route('/profile', methods=['GET'])
def get_profile():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, name, email, phone, address, role, position, experience, is_new, profile_picture, skills, created_at
        FROM users WHERE id = %s
    """, (user['user_id'],))
    profile = cursor.fetchone()
    cursor.close()
    
    if not profile:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(profile), 200

@users_bp.route('/profile', methods=['PUT'])
def update_profile():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')
    address = data.get('address')
    position = data.get('position')
    experience = data.get('experience')
    skills = data.get('skills')
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Update profile
    cursor.execute("""
        UPDATE users 
        SET name = %s, email = %s, phone = %s, address = %s, position = %s, experience = %s, skills = %s, is_new = FALSE
        WHERE id = %s
    """, (name, email, phone, address, position, experience, skills, user['user_id']))
    
    conn.commit()
    cursor.close()
    
    return jsonify({'message': 'Profile updated successfully'}), 200

import time
from werkzeug.utils import secure_filename

@users_bp.route('/profile/upload_picture', methods=['POST'])
def upload_profile_picture():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
        
    if 'profile_picture' not in request.files:
        return jsonify({'error': 'No profile_picture part in request'}), 400
        
    file = request.files['profile_picture']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file:
        filename = secure_filename(file.filename)
        unique_filename = f"{int(time.time())}_{user['user_id']}_{filename}"
        
        # Ensure directory exists (fallback just in case app.py didn't create during import)
        import os
        upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads', 'profile_pics')
        os.makedirs(upload_dir, exist_ok=True)
        
        filepath = os.path.join(upload_dir, unique_filename)
        file.save(filepath)
        
        file_url = f"/uploads/profile_pics/{unique_filename}"
        
        # Update Database
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET profile_picture = %s WHERE id = %s", (file_url, user['user_id']))
        conn.commit()
        cursor.close()
        
        return jsonify({'message': 'Profile picture updated successfully', 'file_url': file_url}), 200

@users_bp.route('/workers', methods=['GET'])
def get_all_workers():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Get all workers with their average ratings
    cursor.execute("""
        SELECT u.id, u.name, u.email, u.phone, u.address, u.position, u.experience, u.is_new,
               AVG(r.rating) as avg_rating,
               COUNT(r.id) as review_count
        FROM users u
        LEFT JOIN reviews r ON u.id = r.worker_id
        WHERE u.role = 'worker'
        GROUP BY u.id
        ORDER BY u.created_at DESC
    """)
    workers = cursor.fetchall()
    
    requested_workers = set()
    if user['role'] == 'provider':
        cursor.execute("""
            SELECT DISTINCT ja.worker_id 
            FROM job_applications ja
            JOIN job_posts jp ON ja.job_id = jp.id
            WHERE jp.provider_id = %s
        """, (user['user_id'],))
        requested_workers = {row['worker_id'] for row in cursor.fetchall()}
        
    for w in workers:
        w['is_requested'] = w['id'] in requested_workers

    cursor.close()
    
    return jsonify(workers), 200

@users_bp.route('/users', methods=['GET'])
@role_required('admin')
def get_all_users():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, name, email, phone, address, role, position, experience, created_at
        FROM users
        ORDER BY created_at DESC
    """)
    users = cursor.fetchall()
    cursor.close()
    
    return jsonify(users), 200

@users_bp.route('/users/<int:user_id>', methods=['DELETE'])
@role_required('admin')
def delete_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
    if not cursor.fetchone():
        cursor.close()
        return jsonify({'error': 'User not found'}), 404
    
    # Delete user (cascade will handle related records)
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    cursor.close()
    
    return jsonify({'message': 'User deleted successfully'}), 200
