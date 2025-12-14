import sqlite3

# Connect to database
conn = sqlite3.connect('tear.db')
cursor = conn.cursor()

# Delete all expenses
cursor.execute('DELETE FROM expenses')
print(f"Eliminados {cursor.rowcount} registros de expenses")

# Delete all income transactions
cursor.execute("DELETE FROM transactions WHERE type='Income'")
print(f"Eliminados {cursor.rowcount} registros de transactions (Income)")

# Commit changes
conn.commit()
conn.close()

print("\nBase de datos limpiada exitosamente!")
print("Ahora puedes probar el modulo de finanzas desde cero.")
