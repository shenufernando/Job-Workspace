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
        SELECT id, name, email, phone, address, role, position, experience, is_new, created_at
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
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Update profile
    cursor.execute("""
        UPDATE users 
        SET name = %s, email = %s, phone = %s, address = %s, position = %s, experience = %s, is_new = FALSE
        WHERE id = %s
    """, (name, email, phone, address, position, experience, user['user_id']))
    
    conn.commit()
    cursor.close()
    
    return jsonify({'message': 'Profile updated successfully'}), 200

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
