import pytest
import json

def test_health_check(client):
    """Test if the app runs and health context returns 200"""
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json['status'] == 'healthy'

def test_register_then_login(client, mock_db):
    """Simulate a user registering, requesting a login token, and accessing a protected route."""
    mock_conn, mock_cursor, mock_dict_cursor = mock_db
    
    # 1. Mock Registration Response (Email doesn't exist yet)
    mock_cursor.fetchone.return_value = None  
    mock_cursor.lastrowid = 1
    
    register_payload = {
        "name": "Test User",
        "email": "test@example.com",
        "phone": "0771234567",
        "address": "Colombo",
        "password": "Password123",
        "confirm_password": "Password123", # Required by the route
        "role": "worker"
    }
    
    res_reg = client.post('/api/register', json=register_payload)
    assert res_reg.status_code == 201
    
    # 2. Mock Login Response (Return dict with verified hash)
    from utils.auth import hash_password
    hashed_pw = hash_password("Password123")
    
    mock_dict_cursor.fetchone.return_value = {
        "id": 1, 
        "name": "Test User", 
        "email": "test@example.com", 
        "password_hash": hashed_pw, 
        "role": "worker"
    }
    
    login_payload = {
        "username_or_email": "test@example.com",
        "password": "Password123"
    }
    
    res_login = client.post('/api/login', json=login_payload)
    assert res_login.status_code == 200
    
    # Extract the token
    token = res_login.json.get("token")
    assert token is not None
    
    # 3. Use the extracted token on a protected route
    headers = {'Authorization': f'Bearer {token}'}
    # Provide the mock user for the /api/profile query
    mock_dict_cursor.fetchone.return_value = {
        "id": 1, "email": "test@example.com", "role": "worker", "name": "Test User"
    }
    
    res_me = client.get('/api/profile', headers=headers)
    assert res_me.status_code == 200
    assert res_me.json['email'] == "test@example.com"

def test_protected_route_requires_auth(client):
    """Verify that a protected route natively blocks requests without a valid JWT token."""
    response = client.get('/api/profile')
    assert response.status_code == 401
    
    data = json.loads(response.data)
    assert 'error' in data
    assert data['error'] == 'Authentication required'
