from flask import Blueprint, request, jsonify
import sys
import os
import smtplib
from email.message import EmailMessage
import threading

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import get_db
from utils.auth import hash_password, verify_password, create_token

def send_login_email(user_email, user_name):
    try:
        sender_email = os.getenv('MAIL_USERNAME')
        sender_password = os.getenv('MAIL_PASSWORD')
        
        if not sender_email or not sender_password:
            print("Mail credentials not found, skipping email notification.")
            return

        msg = EmailMessage()
        msg['Subject'] = "New Login Alert - Job Workspace"
        msg['From'] = sender_email
        msg['To'] = user_email
        msg.set_content(f"Hello {user_name},\n\nA new login was just detected on your Job Workspace account. If this was you, no further action is needed. If you did not authorize this login, please contact support immediately.\n\nBest Regards,\nJob Workspace Team")

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
    except Exception as e:
        print(f"Failed to send login email: {e}")

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        phone = data.get('phone')
        address = data.get('address')
        role = data.get('role')
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        position = data.get('position', '')
        experience = data.get('experience', 0)
        
        # Validation
        if not all([name, email, phone, address, role, password]):
            return jsonify({'error': 'All fields are required'}), 400
        
        if role not in ['worker', 'provider']:
            return jsonify({'error': 'Invalid role'}), 400
        
        if password != confirm_password:
            return jsonify({'error': 'Passwords do not match'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if email exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Email already exists'}), 400
        
        # Hash password
        password_hash = hash_password(password)
        
        # Insert user
        cursor.execute("""
            INSERT INTO users (name, email, phone, address, password_hash, role, position, experience)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (name, email, phone, address, password_hash, role, position, experience))
        
        user_id = cursor.lastrowid
        
        # Create notification
        cursor.execute("""
            INSERT INTO notifications (user_id, type, title, message)
            VALUES (%s, 'welcome', 'Welcome!', 'Your account has been created successfully.')
        """, (user_id,))
        
        conn.commit()
        cursor.close()
        
        return jsonify({
            'message': 'Registration successful',
            'user_id': user_id
        }), 201
        
    except Exception as e:
        print(f"Registration error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
            
        username_or_email = data.get('username_or_email')
        password = data.get('password')
        
        if not username_or_email or not password:
            return jsonify({'error': 'Username/Email and password are required'}), 400
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Find user by email or name
        cursor.execute("""
            SELECT id, name, email, password_hash, role FROM users 
            WHERE email = %s OR name = %s
        """, (username_or_email, username_or_email))
        
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Verify password
        try:
            if not verify_password(password, user['password_hash']):
                cursor.close()
                return jsonify({'error': 'Invalid credentials'}), 401
        except Exception as e:
            cursor.close()
            print(f"Password verification error: {e}")
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Create token
        try:
            token = create_token(user['id'], user['role'])
        except Exception as e:
            cursor.close()
            print(f"Token creation error: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': 'Failed to create authentication token'}), 500
        
        cursor.close()
        
        # Send email notification asynchronously
        if user['role'] in ['worker', 'provider']:
            threading.Thread(target=send_login_email, args=(user['email'], user['name'])).start()
        
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': user['id'],
                'name': user['name'],
                'email': user['email'],
                'role': user['role']
            }
        }), 200
        
    except Exception as e:
        print(f"Login error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Login failed: {str(e)}'}), 500
