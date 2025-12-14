import sqlite3
import hashlib

def update_admin_password():
    db_path = "tear.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Hash the default password 'admin123'
    hashed_password = hashlib.sha256('admin123'.encode()).hexdigest()
    
    # Update the admin user
    cursor.execute("UPDATE users SET password_hash = ? WHERE username = 'admin'", (hashed_password,))
    
    if cursor.rowcount > 0:
        print("Admin password updated successfully.")
    else:
        print("Admin user not found.")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    update_admin_password()
