import pytest
import json
from utils.auth import hash_password

def get_provider_token(client, mock_dict_cursor, mock_cursor):
    """Helper functional simulating the exact Auth Flow explicitly returning a Header mapping"""
    # 1. Mock Registration
    mock_cursor.fetchone.return_value = None
    mock_cursor.lastrowid = 2
    
    register_payload = {
        "name": "Provider Test",
        "email": "provider@test.com",
        "phone": "0771234567",
        "address": "Colombo",
        "password": "Password123",
        "confirm_password": "Password123",
        "role": "provider"
    }
    client.post('/api/register', json=register_payload)
    
    # 2. Mock Login Response
    hashed_pw = hash_password("Password123")
    mock_dict_cursor.fetchone.return_value = {
        "id": 2, "name": "Provider Test", "email": "provider@test.com", 
        "password_hash": hashed_pw, "role": "provider"
    }
    
    login_res = client.post('/api/login', json={"username_or_email": "provider@test.com", "password": "Password123"})
    token = login_res.json.get("token")
    
    # Provide the mock user for any `@jwt_required` endpoints verifying identity
    mock_dict_cursor.fetchone.return_value = {
        "id": 2, "email": "provider@test.com", "role": "provider", "name": "Provider Test"
    }
    
    return {'Authorization': f'Bearer {token}'}

def test_fetch_jobs(client, mock_db):
    """Test fetching all active jobs natively through the JSON bridge."""
    mock_conn, mock_cursor, mock_dict_cursor = mock_db
    
    headers = get_provider_token(client, mock_dict_cursor, mock_cursor)
    
    # Mock database returning a single job instance upon fetch
    mock_dict_cursor.fetchall.return_value = [
        {
            "id": 101,
            "title": "Need a Plumber",
            "description": "Fix my sink",
            "required_skills": "plumbing",
            "budget": 5000,
            "status": "pending",
            "provider_id": 2,
            "provider_name": "Provider Test",
            "created_at": "2023-10-01"
        }
    ]
    
    response = client.get('/api/jobs', headers=headers)
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]['title'] == "Need a Plumber"

def test_post_new_job(client, mock_db):
    """Verify a Provider can successfully post a new job."""
    mock_conn, mock_cursor, mock_dict_cursor = mock_db
    
    headers = get_provider_token(client, mock_dict_cursor, mock_cursor)
    
    payload = {
        "title": "Electrician Needed",
        "description": "Wiring issues in the living room.",
        "skills": "electrical, wiring",
        "location": "colombo",
        "budget": 6000
    }
    
    response = client.post('/api/jobs', headers=headers, json=payload)
    
    assert response.status_code == 201
    assert "successfully" in response.json.get('message', '').lower()

def test_job_completion_payment_flow(client, mock_db):
    """Test the completion logic validating the Payment Modal trigger explicitly."""
    mock_conn, mock_cursor, mock_dict_cursor = mock_db
    
    headers = get_provider_token(client, mock_dict_cursor, mock_cursor)
    
    # Mock checking job existence and ownership (Returns a tuple for normal cursors)
    mock_cursor.fetchone.return_value = (2,)
    
    payload = {
        "payment_method": "card",
        "rating": 5,
        "review": "Excellent work!"
    }
    
    response = client.put('/api/jobs/1/complete', headers=headers, json=payload)
    
    # If successful, it performs multiple internal updates and returns 200
    assert response.status_code == 200
    assert "completed" in response.json.get('message', '').lower()
