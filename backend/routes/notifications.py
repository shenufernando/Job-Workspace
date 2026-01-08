from flask import Blueprint, request, jsonify
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import get_db
from utils.auth import get_current_user

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/notifications', methods=['GET'])
def get_notifications():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT * FROM notifications 
        WHERE user_id = %s 
        ORDER BY created_at DESC
        LIMIT 50
    """, (user['user_id'],))
    
    notifications = cursor.fetchall()
    cursor.close()
    
    return jsonify(notifications), 200

@notifications_bp.route('/notifications/unread', methods=['GET'])
def get_unread_count():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COUNT(*) FROM notifications 
        WHERE user_id = %s AND is_read = FALSE
    """, (user['user_id'],))
    
    count = cursor.fetchone()[0]
    cursor.close()
    
    return jsonify({'unread_count': count}), 200

@notifications_bp.route('/notifications/<int:notification_id>/read', methods=['PUT'])
def mark_as_read(notification_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE notifications 
        SET is_read = TRUE 
        WHERE id = %s AND user_id = %s
    """, (notification_id, user['user_id']))
    
    conn.commit()
    cursor.close()
    
    return jsonify({'message': 'Notification marked as read'}), 200

@notifications_bp.route('/notifications/read-all', methods=['PUT'])
def mark_all_as_read():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE notifications 
        SET is_read = TRUE 
        WHERE user_id = %s AND is_read = FALSE
    """, (user['user_id'],))
    
    conn.commit()
    cursor.close()
    
    return jsonify({'message': 'All notifications marked as read'}), 200
