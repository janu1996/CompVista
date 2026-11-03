
import os
import sqlite3
from pathlib import Path

DB_PATH = os.environ.get(
    "COMPVISTA_DB_PATH",
    "backend/compvista_backup.db"
)

db_file = Path(DB_PATH).resolve()

if not db_file.exists():
    raise FileNotFoundError(f"Database not found: {db_file}")

connection = sqlite3.connect(
    db_file.as_uri() + "?mode=ro",
    uri=True
)
cursor = connection.cursor()

print("\n===== CURRENCY HISTORY AUDIT =====")
print("Database:", db_file.name)

# 1. Salary records by currency
cursor.execute("""
    SELECT currency_code, COUNT(*)
    FROM salary_records
    GROUP BY currency_code
    ORDER BY currency_code
""")

print("\nSalary records by currency:")
for row in cursor.fetchall():
    print(row)

# 2. Compensation bands by currency
cursor.execute("""
    SELECT currency_code, COUNT(*)
    FROM compensation_bands
    GROUP BY currency_code
    ORDER BY currency_code
""")

print("\nCompensation bands by currency:")
for row in cursor.fetchall():
    print(row)

# 3. Employees by location currency
cursor.execute("""
    SELECT
        l.location_name,
        l.currency_code,
        COUNT(DISTINCT e.employee_id)
    FROM employees e
    JOIN locations l
        ON e.location_id = l.location_id
    GROUP BY l.location_name, l.currency_code
    ORDER BY l.location_name
""")

print("\nEmployees by location currency:")
for row in cursor.fetchall():
    print(row)

connection.close()

print("\nCURRENCY AUDIT COMPLETED!")
