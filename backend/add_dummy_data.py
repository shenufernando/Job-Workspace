import sys
import os
from werkzeug.security import generate_password_hash
from datetime import datetime

# Add parent directory to path to allow importing from utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.database import get_db

# අලුතින් app එක import කරමු
from app import app

def seed_data():
    # මෙන්න මේ app_context එක ඇතුලේ තමයි DB එකට connect වෙන්න ඕනේ
    with app.app_context():
        conn = get_db()
        cursor = conn.cursor()

        # හැමෝගෙම Password එක "123456" විදියට සෙට් කරමු
        hashed_pw = generate_password_hash("123456")
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        print("⏳ Adding 10 new Workers...")
        workers = [
            ("Saman Kumara", "saman@test.com", "0711111111", "Colombo", hashed_pw, "worker", "Plumber", 5, 1),
            ("Ruwan Perera", "ruwan@test.com", "0722222222", "Gampaha", hashed_pw, "worker", "Electrician", 3, 1),
            ("Nimal Silva", "nimal@test.com", "0733333333", "Kandy", hashed_pw, "worker", "Carpenter", 8, 1),
            ("Kasun Kalhara", "kasun@test.com", "0744444444", "Galle", hashed_pw, "worker", "Mason", 4, 1),
            ("Ajith Rajapaksha", "ajith@test.com", "0755555555", "Matara", hashed_pw, "worker", "Painter", 6, 1),
            ("Dinesh Fernando", "dinesh@test.com", "0766666666", "Negombo", hashed_pw, "worker", "AC Technician", 2, 1),
            ("Tharindu Lakshan", "tharindu@test.com", "0777777777", "Colombo", hashed_pw, "worker", "Web Developer", 4, 1),
            ("Kavinda Peiris", "kavinda@test.com", "0788888888", "Panadura", hashed_pw, "worker", "Driver", 10, 1),
            ("Suresh Gamlath", "suresh@test.com", "0799999999", "Kurunegala", hashed_pw, "worker", "Gardener", 5, 1),
            ("Nuwan Pradeep", "nuwan@test.com", "0700000000", "Ratnapura", hashed_pw, "worker", "Welder", 7, 1)
        ]
        
        for w in workers:
            try:
                # ඔයාගේ DB එකේ තියෙන columns වලට හරියටම ගැලපෙන්න
                cursor.execute("""
                    INSERT INTO users (name, email, phone, address, password_hash, role, position, experience, is_new)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, w)
            except Exception as e:
                # Email එක දැනටමත් තියෙනවා නම් Error එකක් නොපෙන්වා ඊළඟ එකට යනවා
                pass 

        print("⏳ Adding a Test Provider...")
        try:
            cursor.execute("""
                INSERT INTO users (name, email, phone, address, password_hash, role, is_new)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, ("Test Provider", "provider@test.com", "0712345678", "Colombo", hashed_pw, "provider", 0))
        except:
            pass
            
        # අලුතෙන් හදපු Provider ගේ ID එක ගන්නවා
        cursor.execute("SELECT id FROM users WHERE email = 'provider@test.com'")
        provider_result = cursor.fetchone()
        
        # Admin ගේ ID එක ගන්නවා (Approve කරපු කෙනා විදියට පෙන්නන්න)
        cursor.execute("SELECT id FROM users WHERE role = 'admin' LIMIT 1")
        admin_result = cursor.fetchone()
        admin_id = admin_result[0] if admin_result else 11
        
        if provider_result:
            provider_id = provider_result[0]

            print("⏳ Adding 3 Active Job Posts for the Provider...")
            jobs = [
                (provider_id, "Need a Plumber urgently", "Looking for an experienced plumber to fix a water leak.", "Colombo", 5000, "1 day", 3, 'approved', 'paid', 5000, now, admin_id, now),
                (provider_id, "House Wiring Project", "Complete house wiring for a new build. Need an expert.", "Gampaha", 25000, "1 week", 2, 'approved', 'paid', 25000, now, admin_id, now),
                (provider_id, "Web Developer for E-commerce", "Need a React/Node developer for a new site.", "Remote", 50000, "1 month", 4, 'approved', 'paid', 50000, now, admin_id, now)
            ]

            for j in jobs:
                try:
                    cursor.execute("""
                        INSERT INTO job_posts (provider_id, title, description, location, salary, duration, required_experience, status, payment_status, payment_amount, payment_date, approved_by, approved_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, j)
                except Exception as e:
                    pass

        conn.commit()
        cursor.close()
        print("✅ SUCCESS: Successfully added 10 Workers, 1 Provider, and 3 Active Job Posts!")

if __name__ == "__main__":
    seed_data()