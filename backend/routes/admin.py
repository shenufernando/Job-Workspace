from flask import Blueprint, request, jsonify
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import get_db
from utils.auth import role_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/dashboard', methods=['GET'])
@role_required('admin')
def get_dashboard_stats():
    # Additional check - get current user to verify
    from utils.auth import get_current_user
    current_user = get_current_user()
    print(f"Admin dashboard accessed by user: {current_user}")
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Total users
    cursor.execute("SELECT COUNT(*) as count FROM users WHERE role != 'admin'")
    total_users = cursor.fetchone()['count']
    
    # Total workers
    cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'worker'")
    total_workers = cursor.fetchone()['count']
    
    # Total providers
    cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'provider'")
    total_providers = cursor.fetchone()['count']
    
    # Active jobs
    cursor.execute("SELECT COUNT(*) as count FROM job_posts WHERE status = 'approved'")
    active_jobs = cursor.fetchone()['count']
    
    # Pending jobs
    cursor.execute("SELECT COUNT(*) as count FROM job_posts WHERE status = 'pending'")
    pending_jobs = cursor.fetchone()['count']
    
    # Completed jobs
    cursor.execute("SELECT COUNT(*) as count FROM job_posts WHERE status = 'completed'")
    completed_jobs = cursor.fetchone()['count']
    
    # Total Job Volume
    cursor.execute("SELECT SUM(salary) as total FROM job_posts WHERE status IN ('approved', 'completed')")
    total_job_value = cursor.fetchone()['total'] or 0

    # Platform Revenue (500 LKR per active/completed job)
    cursor.execute("SELECT COUNT(*) as count FROM job_posts WHERE status IN ('approved', 'completed')")
    paid_jobs_count = cursor.fetchone()['count'] or 0
    platform_revenue = paid_jobs_count * 500.0
    
    # Total applications
    cursor.execute("SELECT COUNT(*) as count FROM job_applications")
    total_applications = cursor.fetchone()['count']
    
    cursor.close()
    
    return jsonify({
        'total_users': total_users,
        'total_workers': total_workers,
        'total_providers': total_providers,
        'active_jobs': active_jobs,
        'pending_jobs': pending_jobs,
        'completed_jobs': completed_jobs,
        'total_job_value': float(total_job_value),
        'platform_revenue': float(platform_revenue),
        'total_applications': total_applications
    }), 200

@admin_bp.route('/admin/payments', methods=['GET'])
@role_required('admin')
def get_payments():
    # Only admins can view the dedicated payments dashboard
    from utils.auth import get_current_user
    current_user = get_current_user()
    print(f"Admin payments accessed by user: {current_user}")
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch all jobs that imply a platform fee (approved or completed)
    cursor.execute("""
        SELECT 
            j.id, j.title, 
            p.name as provider_name,
            w.name as worker_name,
            j.salary as job_volume,
            500.0 as platform_fee,
            j.status,
            j.created_at
        FROM job_posts j
        JOIN users p ON j.provider_id = p.id
        LEFT JOIN job_applications a ON j.id = a.job_id AND a.status = 'accepted'
        LEFT JOIN users w ON a.worker_id = w.id
        WHERE j.status IN ('approved', 'completed')
        ORDER BY j.created_at DESC
    """)
    payments = cursor.fetchall()
    cursor.close()
    
    return jsonify(payments), 200
