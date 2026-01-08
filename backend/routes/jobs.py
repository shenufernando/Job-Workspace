from flask import Blueprint, request, jsonify
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import get_db
from utils.auth import get_current_user, role_required
from utils.ai_matching import match_workers_to_job, recommend_jobs_for_worker

jobs_bp = Blueprint('jobs', __name__)

@jobs_bp.route('/jobs', methods=['POST'])
def create_job():
    user = get_current_user()
    if not user or user['role'] != 'provider':
        return jsonify({'error': 'Only providers can create jobs'}), 403
    
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    location = data.get('location')
    salary = data.get('salary')
    duration = data.get('duration')
    required_experience = data.get('required_experience', 0)
    
    if not all([title, description, location]):
        return jsonify({'error': 'Title, description, and location are required'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO job_posts (provider_id, title, description, location, salary, duration, required_experience, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending')
    """, (user['user_id'], title, description, location, salary, duration, required_experience))
    
    job_id = cursor.lastrowid
    
    # Create notification for provider
    cursor.execute("""
        INSERT INTO notifications (user_id, type, title, message, related_id)
        VALUES (%s, 'job_created', 'Job Posted', 'Your job post has been created and is pending payment.', %s)
    """, (user['user_id'], job_id))
    
    conn.commit()
    cursor.close()
    
    return jsonify({
        'message': 'Job created successfully',
        'job_id': job_id
    }), 201

@jobs_bp.route('/jobs', methods=['GET'])
def get_jobs():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Workers see all approved jobs
    if user['role'] == 'worker':
        cursor.execute("""
            SELECT j.*, u.name as provider_name,
                   CASE WHEN ja.id IS NOT NULL THEN TRUE ELSE FALSE END as has_applied,
                   ja.status as application_status
            FROM job_posts j
            JOIN users u ON j.provider_id = u.id
            LEFT JOIN job_applications ja ON j.id = ja.job_id AND ja.worker_id = %s
            WHERE j.status = 'approved'
            ORDER BY j.created_at DESC
        """, (user['user_id'],))
    # Providers see their own jobs
    elif user['role'] == 'provider':
        cursor.execute("""
            SELECT j.*, u.name as provider_name,
                   COUNT(ja.id) as application_count
            FROM job_posts j
            JOIN users u ON j.provider_id = u.id
            LEFT JOIN job_applications ja ON j.id = ja.job_id
            WHERE j.provider_id = %s
            GROUP BY j.id
            ORDER BY j.created_at DESC
        """, (user['user_id'],))
    # Admin sees all jobs
    else:
        cursor.execute("""
            SELECT j.*, u.name as provider_name,
                   COUNT(ja.id) as application_count
            FROM job_posts j
            JOIN users u ON j.provider_id = u.id
            LEFT JOIN job_applications ja ON j.id = ja.job_id
            GROUP BY j.id
            ORDER BY j.created_at DESC
        """)
    
    jobs = cursor.fetchall()
    cursor.close()
    
    return jsonify(jobs), 200

@jobs_bp.route('/jobs/<int:job_id>', methods=['GET'])
def get_job(job_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT j.*, u.name as provider_name
        FROM job_posts j
        JOIN users u ON j.provider_id = u.id
        WHERE j.id = %s
    """, (job_id,))
    job = cursor.fetchone()
    
    if not job:
        cursor.close()
        return jsonify({'error': 'Job not found'}), 404
    
    # Get applications if provider or admin
    if user['role'] in ['provider', 'admin'] and job['provider_id'] == user['user_id']:
        cursor.execute("""
            SELECT ja.*, u.name as worker_name, u.position, u.experience
            FROM job_applications ja
            JOIN users u ON ja.worker_id = u.id
            WHERE ja.job_id = %s
        """, (job_id,))
        job['applications'] = cursor.fetchall()
    
    cursor.close()
    return jsonify(job), 200

@jobs_bp.route('/jobs/<int:job_id>/match', methods=['GET'])
def get_matched_workers(job_id):
    user = get_current_user()
    if not user or user['role'] != 'provider':
        return jsonify({'error': 'Only providers can view matches'}), 403
    
    matched_workers = match_workers_to_job(job_id)
    return jsonify(matched_workers), 200

@jobs_bp.route('/jobs/recommended', methods=['GET'])
def get_recommended_jobs():
    user = get_current_user()
    if not user or user['role'] != 'worker':
        return jsonify({'error': 'Only workers can view recommendations'}), 403
    
    recommended = recommend_jobs_for_worker(user['user_id'])
    return jsonify(recommended), 200

@jobs_bp.route('/jobs/<int:job_id>/apply', methods=['POST'])
def apply_for_job(job_id):
    user = get_current_user()
    if not user or user['role'] != 'worker':
        return jsonify({'error': 'Only workers can apply for jobs'}), 403
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if job exists and is approved
    cursor.execute("SELECT id, provider_id, status FROM job_posts WHERE id = %s", (job_id,))
    job = cursor.fetchone()
    
    if not job:
        cursor.close()
        return jsonify({'error': 'Job not found'}), 404
    
    if job[2] != 'approved':
        cursor.close()
        return jsonify({'error': 'Job is not available for applications'}), 400
    
    # Check if already applied
    cursor.execute("SELECT id FROM job_applications WHERE job_id = %s AND worker_id = %s", (job_id, user['user_id']))
    if cursor.fetchone():
        cursor.close()
        return jsonify({'error': 'Already applied for this job'}), 400
    
    # Create application
    cursor.execute("""
        INSERT INTO job_applications (job_id, worker_id, status)
        VALUES (%s, %s, 'pending')
    """, (job_id, user['user_id']))
    
    # Notify provider
    cursor.execute("""
        INSERT INTO notifications (user_id, type, title, message, related_id)
        VALUES (%s, 'new_application', 'New Application', 'A worker has applied for your job post.', %s)
    """, (job[1], job_id))
    
    conn.commit()
    cursor.close()
    
    return jsonify({'message': 'Application submitted successfully'}), 201

@jobs_bp.route('/jobs/<int:job_id>/applications/<int:application_id>', methods=['PUT'])
def update_application_status(job_id, application_id):
    user = get_current_user()
    if not user or user['role'] != 'provider':
        return jsonify({'error': 'Only providers can update application status'}), 403
    
    data = request.get_json()
    status = data.get('status')
    
    if status not in ['accepted', 'rejected']:
        return jsonify({'error': 'Invalid status'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Verify job belongs to provider
    cursor.execute("SELECT provider_id FROM job_posts WHERE id = %s", (job_id,))
    job = cursor.fetchone()
    
    if not job or job[0] != user['user_id']:
        cursor.close()
        return jsonify({'error': 'Job not found or unauthorized'}), 404
    
    # Update application
    cursor.execute("""
        UPDATE job_applications 
        SET status = %s 
        WHERE id = %s AND job_id = %s
    """, (status, application_id, job_id))
    
    # Get worker ID for notification
    cursor.execute("SELECT worker_id FROM job_applications WHERE id = %s", (application_id,))
    application = cursor.fetchone()
    
    if application:
        # Notify worker
        title = f'Application {status.capitalize()}'
        message = f'Your application has been {status}.'
        cursor.execute("""
            INSERT INTO notifications (user_id, type, title, message, related_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (application[0], f'application_{status}', title, message, job_id))
    
    conn.commit()
    cursor.close()
    
    return jsonify({'message': f'Application {status} successfully'}), 200

@jobs_bp.route('/jobs/<int:job_id>/complete', methods=['PUT'])
def complete_job(job_id):
    user = get_current_user()
    if not user or user['role'] != 'provider':
        return jsonify({'error': 'Only providers can complete jobs'}), 403
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Verify job belongs to provider
    cursor.execute("SELECT provider_id FROM job_posts WHERE id = %s", (job_id,))
    job = cursor.fetchone()
    
    if not job or job[0] != user['user_id']:
        cursor.close()
        return jsonify({'error': 'Job not found or unauthorized'}), 404
    
    # Update job status
    cursor.execute("UPDATE job_posts SET status = 'completed' WHERE id = %s", (job_id,))
    
    conn.commit()
    cursor.close()
    
    return jsonify({'message': 'Job marked as completed'}), 200

@jobs_bp.route('/jobs/<int:job_id>', methods=['PUT'])
@role_required('admin')
def update_job_status(job_id):
    data = request.get_json()
    status = data.get('status')
    
    if status not in ['approved', 'rejected', 'pending']:
        return jsonify({'error': 'Invalid status'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Get job details
    cursor.execute("SELECT provider_id FROM job_posts WHERE id = %s", (job_id,))
    job = cursor.fetchone()
    
    if not job:
        cursor.close()
        return jsonify({'error': 'Job not found'}), 404
    
    # Update status
    if status == 'approved':
        cursor.execute("""
            UPDATE job_posts 
            SET status = 'approved', approved_by = %s, approved_at = NOW()
            WHERE id = %s
        """, (get_current_user()['user_id'], job_id))
    else:
        cursor.execute("UPDATE job_posts SET status = %s WHERE id = %s", (status, job_id))
    
    # Notify provider
    title = f'Job {status.capitalize()}'
    message = f'Your job post has been {status} by admin.'
    cursor.execute("""
        INSERT INTO notifications (user_id, type, title, message, related_id)
        VALUES (%s, %s, %s, %s, %s)
    """, (job[0], f'job_{status}', title, message, job_id))
    
    conn.commit()
    cursor.close()
    
    return jsonify({'message': f'Job {status} successfully'}), 200

@jobs_bp.route('/jobs/<int:job_id>', methods=['DELETE'])
@role_required('admin')
def delete_job(job_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM job_posts WHERE id = %s", (job_id,))
    conn.commit()
    cursor.close()
    
    return jsonify({'message': 'Job deleted successfully'}), 200
