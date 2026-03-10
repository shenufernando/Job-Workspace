from flask import Blueprint, request, jsonify
import sys
import os
import math
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time

# Add parent directory to path to allow importing from utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import get_db
from utils.auth import get_current_user, role_required
from utils.ai_matching import get_ranked_workers 

jobs_bp = Blueprint('jobs', __name__)

# Global cache to optimize Nominatim API requests
geo_cache = {}
geolocator = Nominatim(user_agent="job_workspace_app")

# --- දුර මැනීමේ Function එක (ශ්‍රී ලංකාවේ නගර සඳහා) ---
def calculate_sl_distance(city1, city2):
    if not city1 or not city2:
        return None
        
    l1 = city1.lower().strip()
    l2 = city2.lower().strip()

    # Bail out immediately if explicit remote is passed
    if 'remote' in l1 or 'remote' in l2:
        return None

    c1_coords = None
    c2_coords = None

    # Process City 1
    c1_query = f"{l1}, Sri Lanka"
    if c1_query in geo_cache:
        c1_coords = geo_cache[c1_query]
    else:
        try:
            loc1 = geolocator.geocode(c1_query, timeout=5)
            if loc1:
                c1_coords = (loc1.latitude, loc1.longitude)
                geo_cache[c1_query] = c1_coords
                time.sleep(0.5) # respect rate limit
        except Exception as e:
            print(f"Geocoding Error for {l1}: {e}")

    # Process City 2
    c2_query = f"{l2}, Sri Lanka"
    if c2_query in geo_cache:
        c2_coords = geo_cache[c2_query]
    else:
        try:
            loc2 = geolocator.geocode(c2_query, timeout=5)
            if loc2:
                c2_coords = (loc2.latitude, loc2.longitude)
                geo_cache[c2_query] = c2_coords
                time.sleep(0.5) # respect rate limit
        except Exception as e:
            print(f"Geocoding Error for {l2}: {e}")

    if c1_coords and c2_coords:
        return round(geodesic(c1_coords, c2_coords).km, 1)

    return None
# -------------------------------------------------------

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
    required_skills = data.get('required_skills', '')
    
    if not all([title, description, location]):
        return jsonify({'error': 'Title, description, and location are required'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO job_posts (provider_id, title, description, location, required_skills, salary, duration, required_experience, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending')
    """, (user['user_id'], title, description, location, required_skills, salary, duration, required_experience))
    
    job_id = cursor.lastrowid
    
    cursor.execute("""
        INSERT INTO notifications (user_id, type, title, message, related_id)
        VALUES (%s, 'job_created', 'Job Posted', 'Your job post has been created and is pending approval.', %s)
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
    
    if user['role'] == 'worker':
        cursor.execute("""
            SELECT j.*, u.name as provider_name,
                   CASE WHEN ja.id IS NOT NULL THEN TRUE ELSE FALSE END as has_applied,
                   ja.status as application_status
            FROM job_posts j
            JOIN users u ON j.provider_id = u.id
            LEFT JOIN job_applications ja ON j.id = ja.job_id AND ja.worker_id = %s
            WHERE j.status = 'approved' AND j.payment_status = 'paid'
            ORDER BY j.created_at DESC
        """, (user['user_id'],))
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
    
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM job_posts WHERE id = %s", (job_id,))
        job = cursor.fetchone()
        
        if not job:
            return jsonify({'error': 'Job not found'}), 404

        try:
            cursor.execute("""
                SELECT id, name, email, phone, address, position, experience, role, skills
                FROM users 
                WHERE role = 'worker'
            """)
            workers = cursor.fetchall()
        except Exception as column_err:
            print(f"Schema Error (skills missing?): {column_err}. Falling back to old query...")
            # Column likely doesn't exist, use the fallback
            cursor.execute("""
                SELECT id, name, email, phone, address, position, experience, role
                FROM users 
                WHERE role = 'worker'
            """)
            workers = cursor.fetchall()
            
        print(f"DEBUG: Total workers fetched from DB: {len(workers)}", flush=True)
        
        is_remote_job = job.get('location', '').lower().strip() == 'remote'

        cursor.execute("SELECT worker_id FROM job_applications WHERE job_id = %s", (job_id,))
        existing_applications = {row['worker_id'] for row in cursor.fetchall()}

        for w in workers:
            w['is_requested'] = w['id'] in existing_applications
            if 'skills' not in w:
                w['skills'] = f"{w['position']} related tasks" 
            
            if is_remote_job or w.get('address', '').lower().strip() == 'remote':
                w['distance_km'] = 'remote_job'
            else:
                dist = calculate_sl_distance(job.get('location', ''), w.get('address', ''))
                if dist is not None:
                    w['distance_km'] = dist

        matched_workers = get_ranked_workers(job, workers)
        return jsonify(matched_workers[:10]), 200

    except Exception as e:
        print(f"AI Matching Error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            if 'cursor' in locals(): cursor.close()
            conn.close()

@jobs_bp.route('/jobs/recommended', methods=['GET'])
def get_recommended_jobs():
    user = get_current_user()
    if not user or user['role'] != 'worker':
        return jsonify({'error': 'Only workers can view recommendations'}), 403
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch worker's position
    cursor.execute("SELECT position FROM users WHERE id = %s", (user['user_id'],))
    worker = cursor.fetchone()
    worker_pos = worker.get('position', '').strip() if worker and worker.get('position') else ''
    
    if worker_pos:
        search_term = f"%{worker_pos}%"
        cursor.execute("""
            SELECT j.*, u.name as provider_name
            FROM job_posts j
            JOIN users u ON j.provider_id = u.id
            WHERE j.status='approved' AND j.payment_status='paid'
            AND (j.title LIKE %s OR j.required_skills LIKE %s)
            ORDER BY j.created_at DESC LIMIT 10
        """, (search_term, search_term))
        recommended = cursor.fetchall()
        
        # Fallback if no specific matches found
        if not recommended:
            cursor.execute("""
                SELECT j.*, u.name as provider_name
                FROM job_posts j
                JOIN users u ON j.provider_id = u.id
                WHERE j.status='approved' AND j.payment_status='paid'
                ORDER BY j.created_at DESC LIMIT 5
            """)
            recommended = cursor.fetchall()
    else:
        # If worker has no position, just show latest 5
        cursor.execute("""
            SELECT j.*, u.name as provider_name
            FROM job_posts j
            JOIN users u ON j.provider_id = u.id
            WHERE j.status='approved' AND j.payment_status='paid'
            ORDER BY j.created_at DESC LIMIT 5
        """)
        recommended = cursor.fetchall()
        
    cursor.close()
    
    return jsonify(recommended), 200

@jobs_bp.route('/jobs/<int:job_id>/apply', methods=['POST'])
def apply_for_job(job_id):
    user = get_current_user()
    if not user or user['role'] != 'worker':
        return jsonify({'error': 'Only workers can apply for jobs'}), 403
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, provider_id, status, payment_status FROM job_posts WHERE id = %s", (job_id,))
    job = cursor.fetchone()
    
    if not job:
        cursor.close()
        return jsonify({'error': 'Job not found'}), 404
    
    if job[2] != 'approved' or job[3] != 'paid':
        cursor.close()
        return jsonify({'error': 'Job is not available for applications'}), 400
    
    cursor.execute("SELECT id FROM job_applications WHERE job_id = %s AND worker_id = %s", (job_id, user['user_id']))
    if cursor.fetchone():
        cursor.close()
        return jsonify({'error': 'Already applied for this job'}), 400
    
    cursor.execute("""
        INSERT INTO job_applications (job_id, worker_id, status)
        VALUES (%s, %s, 'pending')
    """, (job_id, user['user_id']))
    
    cursor.execute("""
        INSERT INTO notifications (user_id, type, title, message, related_id)
        VALUES (%s, 'new_application', 'New Application', 'A worker has applied for your job post.', %s)
    """, (job[1], job_id))
    
    conn.commit()
    cursor.close()
    
    return jsonify({'message': 'Application submitted successfully'}), 201

@jobs_bp.route('/jobs/<int:job_id>/invite/<int:worker_id>', methods=['POST'])
def invite_worker(job_id, worker_id):
    user = get_current_user()
    if not user or user['role'] != 'provider':
        return jsonify({'error': 'Only providers can invite workers'}), 403
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True) 
    
    try:
        cursor.execute("SELECT title, provider_id, status, payment_status FROM job_posts WHERE id = %s", (job_id,))
        job = cursor.fetchone()
        
        if not job or job['provider_id'] != user['user_id']:
            return jsonify({'error': 'Job not found or unauthorized'}), 404
            
        if job['status'] != 'approved' or job['payment_status'] != 'paid':
            return jsonify({'error': 'Job must be active and paid to invite workers'}), 400

        cursor.execute("SELECT position FROM users WHERE id = %s AND role = 'worker'", (worker_id,))
        worker = cursor.fetchone()
        
        if not worker:
            return jsonify({'error': 'Worker not found'}), 404
            
        worker_pos = (worker['position'] or '').lower()
        job_title = (job['title'] or '').lower()
        
        if worker_pos not in job_title:
            return jsonify({'error': f"Cannot invite a '{worker['position']}' for a job titled '{job['title']}'."}), 400

        cursor.execute("SELECT id FROM job_applications WHERE job_id = %s AND worker_id = %s", (job_id, worker_id))
        if cursor.fetchone():
            return jsonify({'error': 'Worker is already invited or applied for this job'}), 400
        
        # Insert as 'invited' (Make sure you altered the DB Table ENUM!)
        cursor.execute("""
            INSERT INTO job_applications (job_id, worker_id, status)
            VALUES (%s, %s, 'invited')
        """, (job_id, worker_id))
        
        provider_name = user.get('name', 'A Provider')
        cursor.execute("""
            INSERT INTO notifications (user_id, type, title, message, related_id)
            VALUES (%s, 'job_invite', 'Job Invitation', %s, %s)
        """, (worker_id, f"You have been invited by {provider_name} to apply for the job: {job['title']}", job_id))
        
        conn.commit()
        return jsonify({'message': 'Request sent to worker successfully!'}), 201
        
    except Exception as e:
        print(f"Invite Error: {e}")
        conn.rollback()
        return jsonify({'error': 'Internal Server Error (Did you update the ENUM in DB?)'}), 500
    finally:
        cursor.close()

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
    
    cursor.execute("SELECT provider_id FROM job_posts WHERE id = %s", (job_id,))
    job = cursor.fetchone()
    
    if not job or job[0] != user['user_id']:
        cursor.close()
        return jsonify({'error': 'Job not found or unauthorized'}), 404
    
    cursor.execute("""
        UPDATE job_applications 
        SET status = %s 
        WHERE id = %s AND job_id = %s
    """, (status, application_id, job_id))
    
    cursor.execute("SELECT worker_id FROM job_applications WHERE id = %s", (application_id,))
    application = cursor.fetchone()
    
    if application:
        title = f'Application {status.capitalize()}'
        message = f'Your application has been {status}.'
        cursor.execute("""
            INSERT INTO notifications (user_id, type, title, message, related_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (application[0], f'application_{status}', title, message, job_id))
    
    conn.commit()
    cursor.close()
    
    return jsonify({'message': f'Application {status} successfully'}), 200

@jobs_bp.route('/jobs/<int:job_id>/respond-invite', methods=['PUT'])
def respond_invite(job_id):
    user = get_current_user()
    if not user or user['role'] != 'worker':
        return jsonify({'error': 'Only workers can respond to invitations'}), 403
    
    data = request.get_json()
    status = data.get('status')
    
    if status not in ['accepted', 'rejected']:
        return jsonify({'error': 'Invalid status'}), 400
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Check if an application exists with status 'invited'
        cursor.execute("""
            SELECT id, job_id, worker_id, status 
            FROM job_applications 
            WHERE job_id = %s AND worker_id = %s AND status = 'invited'
        """, (job_id, user['user_id']))
        application = cursor.fetchone()
        
        if not application:
            return jsonify({'error': 'Invitation not found or already responded'}), 404
        
        # Get provider ID to send notification
        cursor.execute("SELECT provider_id, title FROM job_posts WHERE id = %s", (job_id,))
        job = cursor.fetchone()
        
        if not job:
            return jsonify({'error': 'Job not found'}), 404
            
        # Update the status to either 'accepted' or 'rejected'
        cursor.execute("""
            UPDATE job_applications 
            SET status = %s 
            WHERE id = %s
        """, (status, application['id']))
        
        # Insert a notification for the provider
        worker_name = user.get('name', 'A worker')
        title = 'Invitation Accepted' if status == 'accepted' else 'Invitation Declined'
        message = f"{worker_name} has {status} your invitation for the job: {job['title']}."
        
        cursor.execute("""
            INSERT INTO notifications (user_id, type, title, message, related_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (job['provider_id'], f'invite_{status}', title, message, job_id))
        
        conn.commit()
        return jsonify({'message': f'Invitation {status} successfully'}), 200
        
    except Exception as e:
        print(f"Respond Invite Error: {e}")
        conn.rollback()
        return jsonify({'error': 'Internal Server Error'}), 500
    finally:
        cursor.close()

@jobs_bp.route('/jobs/<int:job_id>/complete', methods=['PUT'])
def complete_job(job_id):
    user = get_current_user()
    if not user or user['role'] != 'provider':
        return jsonify({'error': 'Only providers can complete jobs'}), 403
    
    data = request.get_json() or {}
    payment_method = data.get('payment_method')
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT provider_id FROM job_posts WHERE id = %s", (job_id,))
    job = cursor.fetchone()
    
    if not job or job[0] != user['user_id']:
        cursor.close()
        return jsonify({'error': 'Job not found or unauthorized'}), 404
    
    # Update job status to completed, ensure payment_status is paid, and save payment_method
    try:
        cursor.execute(
            "UPDATE job_posts SET status = 'completed', payment_status = 'paid', payment_method = %s WHERE id = %s",
            (payment_method, job_id)
        )
        conn.commit()
    except Exception as e:
        print(f"Error completing job: {e}")
        # If payment_method column doesn't exist, fallback gracefully
        cursor.execute(
            "UPDATE job_posts SET status = 'completed', payment_status = 'paid' WHERE id = %s",
            (job_id,)
        )
        conn.commit()
        
    cursor.close()
    
    return jsonify({'message': 'Job marked as completed and worker paid'}), 200

@jobs_bp.route('/jobs/<int:job_id>', methods=['PUT'])
@role_required('admin')
def update_job_status(job_id):
    data = request.get_json()
    status = data.get('status')
    
    if status not in ['approved', 'rejected', 'pending']:
        return jsonify({'error': 'Invalid status'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT provider_id FROM job_posts WHERE id = %s", (job_id,))
    job = cursor.fetchone()
    
    if not job:
        cursor.close()
        return jsonify({'error': 'Job not found'}), 404
    
    if status == 'approved':
        cursor.execute("""
            UPDATE job_posts 
            SET status = 'approved', approved_by = %s, approved_at = NOW()
            WHERE id = %s
        """, (get_current_user()['user_id'], job_id))
    else:
        cursor.execute("UPDATE job_posts SET status = %s WHERE id = %s", (status, job_id))
    
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

@jobs_bp.route('/jobs/<int:job_id>/pay', methods=['PUT'])
def pay_for_job(job_id):
    user = get_current_user()
    if not user or user['role'] != 'provider':
        return jsonify({'error': 'Only providers can pay for jobs'}), 403

    conn = get_db()
    cursor = conn.cursor()
    
    try:
        data = request.get_json()
        if not data or int(data.get('amount', 0)) != 500:
            return jsonify({"error": "Invalid payment amount. The fixed fee is Rs. 500.00."}), 400

        cursor.execute("SELECT provider_id, status, payment_status FROM job_posts WHERE id = %s", (job_id,))
        job = cursor.fetchone()
        
        if not job or job[0] != user['user_id']:
            return jsonify({'error': 'Job not found or unauthorized'}), 404
            
        if job[1] != 'approved':
             return jsonify({'error': 'Job must be approved by admin before payment'}), 400

        cursor.execute("UPDATE job_posts SET payment_status = 'paid' WHERE id = %s", (job_id,))
        conn.commit()
        
        return jsonify({'message': 'Payment successful! Job is now fully published.'}), 200

    except Exception as e:
        print(f"Error processing payment: {e}")
        conn.rollback()
        return jsonify({'error': 'Internal Server Error'}), 500
    finally:
        cursor.close()