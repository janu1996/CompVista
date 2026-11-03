
import os
import sqlite3
from pathlib import Path

# Use the database path supplied through the environment.
DB_PATH = os.environ.get(
    "COMPVISTA_DB_PATH",
    "backend/compvista_backup.db"
)

db_file = Path(DB_PATH).resolve()

if not db_file.exists():
    raise FileNotFoundError(f"Database not found: {db_file}")

# Open database in READ-ONLY mode.
connection = sqlite3.connect(
    db_file.as_uri() + "?mode=ro",
    uri=True
)

cursor = connection.cursor()

print("\n===== COMPVISTA SALARY HISTORY AUDIT =====")
print("Database:", db_file.name)

# 1. Salary history by year
print("\nSALARY HISTORY YEARS")

cursor.execute("""
    SELECT
        strftime('%Y', effective_from) AS salary_year,
        COUNT(*)
    FROM salary_records
    GROUP BY salary_year
    ORDER BY salary_year
""")

for row in cursor.fetchall():
    print(row)

# 2. Employees with historical FTE changes
cursor.execute("""
    SELECT COUNT(*)
    FROM (
        SELECT employee_id
        FROM salary_records
        GROUP BY employee_id
        HAVING COUNT(DISTINCT fte) > 1
    )
""")

print(
    "\nEmployees with multiple FTE values:",
    cursor.fetchone()[0]
)

# 3. Employees with historical currency changes
cursor.execute("""
    SELECT COUNT(*)
    FROM (
        SELECT employee_id
        FROM salary_records
        GROUP BY employee_id
        HAVING COUNT(DISTINCT currency_code) > 1
    )
""")

print(
    "Employees with multiple currencies:",
    cursor.fetchone()[0]
)

# 4. Total salary records
cursor.execute("SELECT COUNT(*) FROM salary_records")

print("Total salary records:", cursor.fetchone()[0])

connection.close()

print("\nSALARY HISTORY AUDIT COMPLETED!")
