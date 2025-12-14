import sqlite3
import os

DB_NAME = "tear.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False, timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Enable Write-Ahead Logging for better concurrency
    cursor.execute("PRAGMA journal_mode=WAL;")
    
    # Users (Admins and Technicians)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL, -- 'admin' or 'technician'
        full_name TEXT NOT NULL
    )
    ''')

    # Clients
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        phone TEXT UNIQUE NOT NULL,
        address TEXT
    )
    ''')

    # Vehicles
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vehicles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        brand TEXT NOT NULL,
        model TEXT NOT NULL,
        year INTEGER NOT NULL,
        plate TEXT UNIQUE NOT NULL,
        details TEXT,
        FOREIGN KEY (client_id) REFERENCES clients (id)
    )
    ''')

    # Services
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL
    )
    ''')

    # Parts (Refacciones)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS parts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        stock INTEGER DEFAULT 0,
        base_price REAL NOT NULL
    )
    ''')

    # Technicians (Employees)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS technicians (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        phone TEXT NOT NULL
    )
    ''')

    # Tools
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tools (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        quantity INTEGER DEFAULT 1
    )
    ''')

    # Repairs
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS repairs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_id INTEGER NOT NULL,
        technician_id INTEGER NOT NULL,
        status TEXT NOT NULL, -- 'En Proceso', 'Completada', 'Cancelada'
        general_details TEXT,
        start_date TEXT,
        end_date TEXT,
        total_cost REAL DEFAULT 0,
        FOREIGN KEY (vehicle_id) REFERENCES vehicles (id),
        FOREIGN KEY (technician_id) REFERENCES technicians (id)
    )
    ''')

    # Repair Services (Many-to-Many)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS repair_services (
        repair_id INTEGER NOT NULL,
        service_id INTEGER NOT NULL,
        price_at_moment REAL NOT NULL,
        FOREIGN KEY (repair_id) REFERENCES repairs (id),
        FOREIGN KEY (service_id) REFERENCES services (id)
    )
    ''')

    # Repair Parts (Many-to-Many)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS repair_parts (
        repair_id INTEGER NOT NULL,
        part_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        price_at_moment REAL NOT NULL,
        FOREIGN KEY (repair_id) REFERENCES repairs (id),
        FOREIGN KEY (part_id) REFERENCES parts (id)
    )
    ''')

    # Invoices
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        repair_id INTEGER NOT NULL,
        issue_date TEXT NOT NULL,
        total_amount REAL NOT NULL,
        pdf_path TEXT,
        FOREIGN KEY (repair_id) REFERENCES repairs (id)
    )
    ''')

    # Transactions (Income/Expenses)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL, -- 'Income' or 'Expense'
        amount REAL NOT NULL,
        description TEXT,
        date TEXT NOT NULL,
        related_repair_id INTEGER,
        FOREIGN KEY (related_repair_id) REFERENCES repairs (id)
    )
    ''')

    # Repair Expenses (Extra costs like towing, etc.)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS repair_expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        repair_id INTEGER NOT NULL,
        description TEXT NOT NULL,
        amount REAL NOT NULL,
        FOREIGN KEY (repair_id) REFERENCES repairs (id)
    )
    ''')

    # General Expenses (New Table)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        amount REAL NOT NULL,
        period_type TEXT NOT NULL, -- 'Semanal', 'Mensual', 'Único'
        date TEXT NOT NULL,
        description TEXT
    )
    ''')
    
    # Seed default admin user if not exists
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        import hashlib
        hashed_password = hashlib.sha256('admin123'.encode()).hexdigest()
        cursor.execute("INSERT INTO users (username, password_hash, role, full_name) VALUES (?, ?, ?, ?)",
                       ('admin', hashed_password, 'admin', 'Administrador Principal'))

    # Migration: Add photo_path to vehicles if not exists
    try:
        cursor.execute("ALTER TABLE vehicles ADD COLUMN photo_path TEXT")
    except sqlite3.OperationalError:
        pass # Column already exists

    # Create vehicle_history table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vehicle_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_id INTEGER NOT NULL,
        description TEXT,
        photo_path TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (vehicle_id) REFERENCES vehicles (id)
    )
    ''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
