from flask import Blueprint, request, jsonify
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import get_db
from utils.auth import get_current_user, role_required

payments_bp = Blueprint('payments', __name__)

@payments_bp.route('/payments', methods=['POST'])
def create_payment():
    user = get_current_user()
    if not user or user['role'] != 'provider':
        return jsonify({'error': 'Only providers can make payments'}), 403
    
    data = request.get_json()
    job_id = data.get('job_id')
    amount = data.get('amount')
    payment_method = data.get('payment_method', 'online')
    
    if not job_id or not amount:
        return jsonify({'error': 'Job ID and amount are required'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Verify job belongs to provider
    cursor.execute("SELECT provider_id, status FROM job_posts WHERE id = %s", (job_id,))
    job = cursor.fetchone()
    
    if not job or job[0] != user['user_id']:
        cursor.close()
        return jsonify({'error': 'Job not found or unauthorized'}), 404
    
    if job[1] != 'pending':
        cursor.close()
        return jsonify({'error': 'Job is not in pending status'}), 400
    
    # Create payment record
    transaction_id = f"TXN{job_id}{user['user_id']}{int(__import__('time').time())}"
    
    cursor.execute("""
        INSERT INTO payments (job_id, provider_id, amount, payment_method, transaction_id, status)
        VALUES (%s, %s, %s, %s, %s, 'completed')
    """, (job_id, user['user_id'], amount, payment_method, transaction_id))
    
    # Update job payment status
    cursor.execute("""
        UPDATE job_posts 
        SET payment_status = 'paid', payment_amount = %s, payment_date = NOW()
        WHERE id = %s
    """, (amount, job_id))
    
    # Notify admin
    cursor.execute("SELECT id FROM users WHERE role = 'admin' LIMIT 1")
    admin = cursor.fetchone()
    if admin:
        cursor.execute("""
            INSERT INTO notifications (user_id, type, title, message, related_id)
            VALUES (%s, 'payment_received', 'Payment Received', 'A new payment has been received for job post review.', %s)
        """, (admin[0], job_id))
    
    conn.commit()
    cursor.close()
    
    return jsonify({
        'message': 'Payment processed successfully',
        'transaction_id': transaction_id
    }), 201

@payments_bp.route('/payments', methods=['GET'])
def get_payments():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    if user['role'] == 'admin':
        cursor.execute("""
            SELECT p.*, j.title as job_title, u.name as provider_name
            FROM payments p
            JOIN job_posts j ON p.job_id = j.id
            JOIN users u ON p.provider_id = u.id
            ORDER BY p.created_at DESC
        """)
    else:
        cursor.execute("""
            SELECT p.*, j.title as job_title
            FROM payments p
            JOIN job_posts j ON p.job_id = j.id
            WHERE p.provider_id = %s
            ORDER BY p.created_at DESC
        """, (user['user_id'],))
    
    payments = cursor.fetchall()
    cursor.close()
    
    return jsonify(payments), 200

