"""
Script to create admin user
Run this script to create an admin user in the database
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from utils.database import get_db
from utils.auth import hash_password

def create_admin():
    print("Creating admin user...")
    with app.app_context():
        name = input("Enter admin name: ")
        email = input("Enter admin email: ")
        phone = input("Enter admin phone: ")
        address = input("Enter admin address: ")
        password = input("Enter admin password: ")
        
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            # Check if email exists
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                print("Error: Email already exists!")
                cursor.close()
                return
            
            # Hash password
            password_hash = hash_password(password)
            
            # Insert admin
            cursor.execute("""
                INSERT INTO users (name, email, phone, address, password_hash, role)
                VALUES (%s, %s, %s, %s, %s, 'admin')
            """, (name, email, phone, address, password_hash))
            
            conn.commit()
            cursor.close()
            
            print("Admin user created successfully!")
        except Exception as e:
            print(f"Error creating admin: {e}")

if __name__ == '__main__':
    create_admin()

