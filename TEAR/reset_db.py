import os
from database import init_db, DB_NAME

def reset_database():
    if os.path.exists(DB_NAME):
        try:
            os.remove(DB_NAME)
            print(f"Database '{DB_NAME}' deleted.")
        except PermissionError:
            print(f"Error: Could not delete '{DB_NAME}'. It might be in use by another process.")
            return

    print("Initializing new database...")
    init_db()
    print("Database reset successfully. Default admin user created.")

if __name__ == "__main__":
    reset_database()