
import sqlite3
import shutil
from pathlib import Path

DB_PATH = Path("backend/compvista_salary_migration_test.db")
BACKUP_PATH = Path(
    "backend/compvista_salary_migration_test_before_changes.db"
)

TARGET_YEARS = (2024, 2025, 2026)

# Only selected employees will receive historical FTE changes.
# This is a documented synthetic scenario, not random corruption.
FTE_CHANGE_EMPLOYEES = {
    "EMP-000010",
    "EMP-000020",
    "EMP-000030",
    "EMP-000040",
    "EMP-000050",
}


def validate_database(cursor):

    checks = {}

    cursor.execute("""
        SELECT COUNT(*)
        FROM salary_records
        WHERE fte <= 0 OR fte > 1
    """)
    checks["Invalid FTE"] = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM salary_records
        WHERE base_salary <= 0
    """)
    checks["Invalid salary"] = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM salary_records s
        LEFT JOIN employees e
            ON s.employee_id = e.employee_id
        WHERE e.employee_id IS NULL
    """)
    checks["Invalid employee FK"] = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM salary_records s
        LEFT JOIN compensation_bands b
            ON s.band_id = b.band_id
        WHERE b.band_id IS NULL
    """)
    checks["Invalid band FK"] = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM salary_records
        WHERE effective_to IS NOT NULL
        AND effective_to <= effective_from
    """)
    checks["Invalid effective dates"] = cursor.fetchone()[0]

    return checks


def main():

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}"
        )

    if BACKUP_PATH.exists():
        raise FileExistsError(
            f"Migration backup already exists: {BACKUP_PATH}"
        )

    # Create a fresh backup before making any changes.
    shutil.copy2(DB_PATH, BACKUP_PATH)

    print("CompVista Salary History Migration")
    print("----------------------------------")
    print("Database:", DB_PATH)
    print("Backup:", BACKUP_PATH)

    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")

    try:

        cursor = connection.cursor()

        cursor.execute("""
            SELECT COUNT(*)
            FROM salary_records
        """)
        before_count = cursor.fetchone()[0]

        print("\nSalary records before:", before_count)

        # Check whether expected salary years exist.
        cursor.execute("""
            SELECT DISTINCT strftime('%Y', effective_from)
            FROM salary_records
            ORDER BY 1
        """)

        years_before = [
            row[0] for row in cursor.fetchall()
        ]

        print("Years before:", years_before)

        # Remove 2023 salary records only.
        # This migration does not alter other years.
        cursor.execute("""
            DELETE FROM salary_records
            WHERE strftime('%Y', effective_from) = '2023'
        """)

        deleted_2023 = cursor.rowcount

        # Apply documented FTE changes to selected employees.
        fte_updated = 0

        for employee_id in sorted(FTE_CHANGE_EMPLOYEES):

            cursor.execute("""
                SELECT salary_id, base_salary, fte
                FROM salary_records
                WHERE employee_id = ?
                  AND strftime('%Y', effective_from)
                      IN ('2024', '2025', '2026')
                ORDER BY effective_from
            """, (employee_id,))

            records = cursor.fetchall()

            if len(records) < 2:
                continue

            previous_fte = None

            for index, (salary_id, base_salary, old_fte) in enumerate(records):

                # Keep first historical FTE.
                if index == 0:
                    new_fte = float(old_fte)
                else:
                    # Alternate between full-time and part-time.
                    new_fte = (
                        0.75 if previous_fte == 1.0
                        else 1.0
                    )

                # Preserve FTE for first record.
                # Change subsequent records only.
                if index > 0 and new_fte != float(old_fte):

                    new_salary = round(
                        float(base_salary)
                        / float(old_fte)
                        * new_fte,
                        2
                    )

                    cursor.execute("""
                        UPDATE salary_records
                        SET fte = ?,
                            base_salary = ?,
                            change_reason =
                                'Synthetic historical FTE change'
                        WHERE salary_id = ?
                    """, (
                        new_fte,
                        new_salary,
                        salary_id
                    ))

                    fte_updated += 1

                previous_fte = new_fte

        # Verify salary years after migration.
        cursor.execute("""
            SELECT DISTINCT strftime('%Y', effective_from)
            FROM salary_records
            ORDER BY 1
        """)

        years_after = [
            row[0] for row in cursor.fetchall()
        ]

        cursor.execute("""
            SELECT COUNT(*)
            FROM salary_records
        """)

        after_count = cursor.fetchone()[0]

        checks = validate_database(cursor)

        print("\nMigration results")
        print("-----------------")
        print("2023 records removed:", deleted_2023)
        print("FTE records updated:", fte_updated)
        print("Salary records after:", after_count)
        print("Years after:", years_after)

        print("\nValidation")
        print("----------")

        for name, count in checks.items():
            print(f"{name}: {count}")

        if any(checks.values()):
            raise RuntimeError(
                "Validation failed. Migration will be rolled back."
            )

        if years_after != ["2024", "2025", "2026"]:
            raise RuntimeError(
                "Unexpected salary history years."
            )

        connection.commit()

        print("\nMIGRATION SUCCESSFUL")

    except Exception:

        connection.rollback()

        # Restore the database from the backup if anything fails.
        connection.close()
        shutil.copy2(BACKUP_PATH, DB_PATH)

        print("\nMigration failed. Backup restored.")
        raise

    finally:

        try:
            connection.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
