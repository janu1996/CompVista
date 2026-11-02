
import sqlite3

DB_PATH = "backend/compvista_salary_migration_test.db"

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

print("\n===== CURRENCY HISTORY AUDIT =====")

cursor.execute("""
    SELECT currency_code, COUNT(*)
    FROM salary_records
    GROUP BY currency_code
    ORDER BY currency_code
""")

print("\nSalary records by currency:")
for row in cursor.fetchall():
    print(row)

cursor.execute("""
    SELECT currency_code, COUNT(*)
    FROM compensation_bands
    GROUP BY currency_code
    ORDER BY currency_code
""")

print("\nCompensation bands by currency:")
for row in cursor.fetchall():
    print(row)

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
