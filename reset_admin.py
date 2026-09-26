import sys
import os

# Add root directory to python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.database import get_session
from models.user import User
from utils.encryption import hash_password

def reset_admin_password(new_password: str):
    with get_session() as session:
        # Find the admin user
        admin = session.query(User).filter(User.username == 'admin').first()
        
        if not admin:
            print("Error: Admin user not found in the database.")
            return
            
        print(f"Found admin user: {admin.first_name} {admin.last_name}")
        
        # Hash and update password
        admin.password_hash = hash_password(new_password)
        admin.is_locked = False
        admin.failed_login_attempts = 0
        
        session.commit()
        print(f"Success! The password for 'admin' has been reset to: '{new_password}'")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        new_password = sys.argv[1]
        reset_admin_password(new_password)
    else:
        print("Usage: python reset_admin.py <new_password>")
