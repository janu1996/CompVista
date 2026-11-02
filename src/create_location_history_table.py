
import sqlite3
from pathlib import Path

DB_PATH = Path("backend/compvista_salary_migration_test.db")

def main():

    if not DB_PATH.exists():
        raise FileNotFoundError(DB_PATH)

    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employee_location_history (
                history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id VARCHAR(20) NOT NULL,
                location_id INTEGER NOT NULL,
                effective_from DATE NOT NULL,
                effective_to DATE,
                change_reason VARCHAR(200) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (employee_id)
                    REFERENCES employees(employee_id),

                FOREIGN KEY (location_id)
                    REFERENCES locations(location_id),

                CHECK (
                    effective_to IS NULL
                    OR effective_to > effective_from
                )
            )
        """)

        # Add initial location history for existing employees.
        cursor.execute("""
            INSERT INTO employee_location_history (
                employee_id,
                location_id,
                effective_from,
                effective_to,
                change_reason
            )
            SELECT
                e.employee_id,
                e.location_id,
                e.hire_date,
                NULL,
                'Initial location assignment'
            FROM employees e
            WHERE NOT EXISTS (
                SELECT 1
                FROM employee_location_history h
                WHERE h.employee_id = e.employee_id
            )
        """)

        inserted = cursor.rowcount

        cursor.execute("""
            SELECT COUNT(*)
            FROM employee_location_history
        """)

        total = cursor.fetchone()[0]

        cursor.execute("""
            PRAGMA foreign_key_check
        """)

        fk_errors = cursor.fetchall()

        if fk_errors:
            raise RuntimeError(
                f"Foreign key validation failed: {fk_errors}"
            )

        connection.commit()

        print("LOCATION HISTORY TABLE CREATED")
        print("New initial history records:", inserted)
        print("Total location history records:", total)
        print("Foreign key errors:", len(fk_errors))
        print("MIGRATION SUCCESSFUL")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()
