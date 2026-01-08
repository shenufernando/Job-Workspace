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
    
    # Total payments
    cursor.execute("SELECT SUM(amount) as total FROM payments WHERE status = 'completed'")
    total_payments = cursor.fetchone()['total'] or 0
    
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
        'total_payments': float(total_payments),
        'total_applications': total_applications
    }), 200

