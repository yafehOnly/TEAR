import sqlite3

def check_db():
    try:
        conn = sqlite3.connect('tear.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM transactions WHERE type='Income'")
        income_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM expenses")
        expense_count = cursor.fetchone()[0]
        
        print(f"Income count: {income_count}")
        print(f"Expense count: {expense_count}")
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_db()
