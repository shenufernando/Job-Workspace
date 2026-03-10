import sys
import os
import bcrypt

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.database import get_db
from app import app

def fix_passwords():
    with app.app_context():
        conn = get_db()
        cursor = conn.cursor()
        
        # ඔයාගේ System එකට ගැලපෙන විදියට '123456' පාස්වර්ඩ් එක හදනවා (bcrypt)
        hashed_pw = bcrypt.hashpw('123456'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # @test.com තියෙන අලුත් යුසර්ස්ලගේ පාස්වර්ඩ් එක Update කරනවා
        cursor.execute("UPDATE users SET password_hash = %s WHERE email LIKE '%@test.com'", (hashed_pw,))
        
        conn.commit()
        cursor.close()
        print("✅ SUCCESS: All Test User Passwords have been fixed! You can now login using '123456'.")

if __name__ == "__main__":
    fix_passwords()