from flask import Blueprint, request, jsonify
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import get_db
from utils.auth import get_current_user, role_required

reviews_bp = Blueprint('reviews', __name__)

@reviews_bp.route('/reviews', methods=['POST'])
def create_review():
    user = get_current_user()
    if not user or user['role'] != 'provider':
        return jsonify({'error': 'Only providers can create reviews'}), 403
    
    data = request.get_json()
    job_id = data.get('job_id')
    worker_id = data.get('worker_id')
    rating = data.get('rating')
    comment = data.get('comment', '')
    
    if not all([job_id, worker_id, rating]):
        return jsonify({'error': 'Job ID, Worker ID, and rating are required'}), 400
    
    if not (1 <= rating <= 5):
        return jsonify({'error': 'Rating must be between 1 and 5'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Verify job belongs to provider and is completed
    cursor.execute("SELECT provider_id, status FROM job_posts WHERE id = %s", (job_id,))
    job = cursor.fetchone()
    
    if not job or job[0] != user['user_id']:
        cursor.close()
        return jsonify({'error': 'Job not found or unauthorized'}), 404
    
    if job[1] != 'completed':
        cursor.close()
        return jsonify({'error': 'Job must be completed before reviewing'}), 400
    
    # Check if review already exists
    cursor.execute("SELECT id FROM reviews WHERE job_id = %s AND worker_id = %s", (job_id, worker_id))
    if cursor.fetchone():
        cursor.close()
        return jsonify({'error': 'Review already exists for this job'}), 400
    
    # Create review
    cursor.execute("""
        INSERT INTO reviews (job_id, worker_id, provider_id, rating, comment)
        VALUES (%s, %s, %s, %s, %s)
    """, (job_id, worker_id, user['user_id'], rating, comment))
    
    # Notify worker
    cursor.execute("""
        INSERT INTO notifications (user_id, type, title, message, related_id)
        VALUES (%s, 'new_review', 'New Review', 'You have received a new review.', %s)
    """, (worker_id, job_id))
    
    conn.commit()
    cursor.close()
    
    return jsonify({'message': 'Review created successfully'}), 201

@reviews_bp.route('/reviews/worker/<int:worker_id>', methods=['GET'])
def get_worker_reviews(worker_id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT r.*, j.title as job_title, u.name as provider_name
        FROM reviews r
        JOIN job_posts j ON r.job_id = j.id
        JOIN users u ON r.provider_id = u.id
        WHERE r.worker_id = %s
        ORDER BY r.created_at DESC
    """, (worker_id,))
    
    reviews = cursor.fetchall()
    cursor.close()
    
    return jsonify(reviews), 200

@reviews_bp.route('/reviews', methods=['GET'])
@role_required('admin')
def get_all_reviews():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT r.*, j.title as job_title, 
               w.name as worker_name, p.name as provider_name
        FROM reviews r
        JOIN job_posts j ON r.job_id = j.id
        JOIN users w ON r.worker_id = w.id
        JOIN users p ON r.provider_id = p.id
        ORDER BY r.created_at DESC
    """)
    
    reviews = cursor.fetchall()
    cursor.close()
    
    return jsonify(reviews), 200

@reviews_bp.route('/reviews/<int:review_id>', methods=['DELETE'])
@role_required('admin')
def delete_review(review_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM reviews WHERE id = %s", (review_id,))
    conn.commit()
    cursor.close()
    
    return jsonify({'message': 'Review deleted successfully'}), 200

