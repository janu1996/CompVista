
import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

configured_path = os.getenv("COMPVISTA_DB_PATH")

if configured_path:
    DB_PATH = Path(configured_path)
    if not DB_PATH.is_absolute():
        DB_PATH = PROJECT_ROOT / DB_PATH
else:
    DB_PATH = BASE_DIR / "compvista_backup.db"


if not DB_PATH.exists():
    raise FileNotFoundError(f"Database not found: {DB_PATH}")

connection = sqlite3.connect(DB_PATH)

try:
    connection.execute("PRAGMA foreign_keys = ON")

    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }

    if "employees" not in tables:
        raise RuntimeError("Employees table not found. Migration stopped.")

    existing_employee_count = connection.execute(
        "SELECT COUNT(*) FROM employees"
    ).fetchone()[0]

    if "users" not in tables:
        connection.execute("""
            CREATE TABLE users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                email VARCHAR(150) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) NOT NULL DEFAULT 'CANDIDATE'
                    CHECK (role IN ('CANDIDATE', 'HR', 'ADMIN')),
                employee_id VARCHAR(20) UNIQUE,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id)
                    REFERENCES employees(employee_id)
            )
        """)

        connection.execute("""
            CREATE INDEX ix_users_email ON users(email)
        """)

        connection.commit()
        print("New users table created successfully!")

    else:
        print("Users table already exists. No changes made.")

    user_count = connection.execute(
        "SELECT COUNT(*) FROM users"
    ).fetchone()[0]

    print("Database:", DB_PATH)
    print("Existing employees preserved:", existing_employee_count)
    print("Current user accounts:", user_count)

except Exception:
    connection.rollback()
    raise

finally:
    connection.close()
