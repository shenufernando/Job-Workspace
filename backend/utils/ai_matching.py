from geopy.distance import geodesic
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import get_db

def calculate_distance(loc1, loc2):
    """Calculate distance between two locations (lat, lon)"""
    try:
        return geodesic(loc1, loc2).kilometers
    except:
        return float('inf')

def get_location_coords(location):
    """Convert location string to coordinates (simplified - in production use geocoding API)"""
    # This is a placeholder - in production, use a geocoding service
    # For now, return a default coordinate
    return (6.9271, 79.8612)  # Default to Colombo, Sri Lanka

def match_workers_to_job(job_id):
    """AI matching algorithm to suggest best workers for a job"""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Get job details
    cursor.execute("""
        SELECT id, provider_id, title, description, location, required_experience, salary
        FROM job_posts WHERE id = %s AND status = 'approved'
    """, (job_id,))
    job = cursor.fetchone()
    
    if not job:
        return []
    
    # Get all active workers
    cursor.execute("""
        SELECT u.id, u.name, u.position, u.experience, u.address,
               AVG(r.rating) as avg_rating,
               COUNT(r.id) as review_count
        FROM users u
        LEFT JOIN reviews r ON u.id = r.worker_id
        WHERE u.role = 'worker'
        GROUP BY u.id
    """)
    workers = cursor.fetchall()
    
    # Get job location coordinates
    job_coords = get_location_coords(job['location'])
    
    # Score each worker
    scored_workers = []
    for worker in workers:
        score = 0
        
        # Experience match (0-40 points)
        if worker['experience'] >= job['required_experience']:
            score += 40
        else:
            score += (worker['experience'] / max(job['required_experience'], 1)) * 40
        
        # Rating score (0-30 points)
        avg_rating = worker['avg_rating'] or 0
        score += (avg_rating / 5) * 30
        
        # Review count bonus (0-10 points)
        review_count = worker['review_count'] or 0
        score += min(review_count * 2, 10)
        
        # Location proximity (0-20 points)
        worker_coords = get_location_coords(worker['address'])
        distance = calculate_distance(job_coords, worker_coords)
        if distance < 5:
            score += 20
        elif distance < 10:
            score += 15
        elif distance < 20:
            score += 10
        else:
            score += max(0, 20 - distance / 5)
        
        # Check if already applied
        cursor.execute("""
            SELECT id FROM job_applications 
            WHERE job_id = %s AND worker_id = %s
        """, (job_id, worker['id']))
        already_applied = cursor.fetchone()
        
        if not already_applied:
            scored_workers.append({
                'worker': worker,
                'score': score,
                'distance': distance
            })
    
    # Sort by score (descending)
    scored_workers.sort(key=lambda x: x['score'], reverse=True)
    
    # Return top 10 matches
    cursor.close()
    return [w['worker'] for w in scored_workers[:10]]

def recommend_jobs_for_worker(worker_id):
    """Recommend jobs for a worker based on their profile"""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Get worker details
    cursor.execute("""
        SELECT id, position, experience, address FROM users WHERE id = %s
    """, (worker_id,))
    worker = cursor.fetchone()
    
    if not worker:
        return []
    
    # Get available jobs
    cursor.execute("""
        SELECT j.*, u.name as provider_name
        FROM job_posts j
        JOIN users u ON j.provider_id = u.id
        WHERE j.status = 'approved'
        AND j.id NOT IN (
            SELECT job_id FROM job_applications WHERE worker_id = %s
        )
    """, (worker_id,))
    jobs = cursor.fetchall()
    
    # Get worker location
    worker_coords = get_location_coords(worker['address'])
    
    # Score each job
    scored_jobs = []
    for job in jobs:
        score = 0
        
        # Experience match
        if worker['experience'] >= job['required_experience']:
            score += 50
        
        # Location proximity
        job_coords = get_location_coords(job['location'])
        distance = calculate_distance(worker_coords, job_coords)
        if distance < 5:
            score += 30
        elif distance < 10:
            score += 20
        elif distance < 20:
            score += 10
        
        # Salary consideration (higher salary = higher score)
        if job['salary']:
            score += min(job['salary'] / 1000, 20)
        
        scored_jobs.append({
            'job': job,
            'score': score,
            'distance': distance
        })
    
    # Sort by score
    scored_jobs.sort(key=lambda x: x['score'], reverse=True)
    cursor.close()
    
    return [j['job'] for j in scored_jobs[:10]]
