
import sqlite3

DB_PATH = "backend/compvista_salary_migration_test.db"

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

print("\nCOMPVISTA SALARY MIGRATION VERIFICATION")
print("---------------------------------------")

cursor.execute("""
    SELECT
        employee_id,
        COUNT(*) AS salary_records,
        COUNT(DISTINCT fte) AS fte_values,
        GROUP_CONCAT(DISTINCT fte) AS fte_history
    FROM salary_records
    GROUP BY employee_id
    HAVING COUNT(DISTINCT fte) > 1
    ORDER BY employee_id
""")

rows = cursor.fetchall()

print("\nEmployees with historical FTE changes:")

for row in rows:
    print(row)

print("\nTotal employees with FTE changes:", len(rows))

cursor.execute("""
    SELECT
        strftime('%Y', effective_from),
        COUNT(*)
    FROM salary_records
    GROUP BY strftime('%Y', effective_from)
    ORDER BY 1
""")

print("\nSalary records by year:")

for row in cursor.fetchall():
    print(row)

cursor.execute("""
    SELECT COUNT(*)
    FROM salary_records
    WHERE change_reason = 'Synthetic historical FTE change'
""")

print(
    "\nRecords marked as FTE changes:",
    cursor.fetchone()[0]
)

connection.close()

print("\nVERIFICATION COMPLETED!")
