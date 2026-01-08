import bcrypt
from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import create_access_token, get_jwt_identity, verify_jwt_in_request, get_jwt
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import get_db

def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id, role):
    """Create JWT token for user"""
    # Flask-JWT-Extended requires identity to be a string/int, not a dict
    # Store additional data in additional_claims
    additional_claims = {'role': role, 'user_id': user_id}
    return create_access_token(identity=str(user_id), additional_claims=additional_claims)

def get_current_user():
    """Get current authenticated user"""
    try:
        verify_jwt_in_request()
        identity = get_jwt_identity()
        
        if not identity:
            print("get_current_user: No identity found")
            return None
        
        # Get additional claims (role, user_id)
        from flask_jwt_extended import get_jwt
        claims = get_jwt()
        
        # Build user dict from identity and claims
        user = {
            'user_id': int(identity) if identity else None,
            'role': claims.get('role') if claims else None
        }
        
        if not user['user_id'] or not user['role']:
            print(f"get_current_user: Missing data - identity: {identity}, claims: {claims}")
            return None
        
        return user
    except Exception as e:
        print(f"JWT verification error in get_current_user: {e}")
        import traceback
        traceback.print_exc()
        return None

def role_required(*roles):
    """Decorator to require specific roles"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                verify_jwt_in_request()
                
                # Get role from JWT claims
                from flask_jwt_extended import get_jwt
                claims = get_jwt()
                user_role = claims.get('role')
                
                if not user_role:
                    print(f"No role found in JWT claims: {claims}")
                    return jsonify({'error': 'Invalid token structure'}), 401
                
                if user_role not in roles:
                    print(f"Role {user_role} not in required roles {roles}")
                    return jsonify({'error': 'Insufficient permissions'}), 403
                
                return f(*args, **kwargs)
            except Exception as e:
                print(f"Role required decorator error: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({'error': 'Authentication failed'}), 401
        return decorated_function
    return decorator

def get_user_by_id(user_id):
    """Get user by ID"""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, email, phone, address, role, position, experience, is_new FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    return user

