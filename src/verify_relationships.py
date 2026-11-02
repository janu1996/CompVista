
import os
import sys

os.environ["COMPVISTA_DB_PATH"] = "backend/compvista_upgrade_test.db"

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_PATH = os.path.join(PROJECT_ROOT, "backend")

if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

from app import app
from extensions import db
from sqlalchemy import text


def verify_relationships():
    with app.app_context():

        print("\n========== COMPVISTA RELATIONSHIP VALIDATION ==========")

        checks = {
            "SalaryRecord -> Employee": """
                SELECT COUNT(*) FROM salary_records s
                LEFT JOIN employees e ON s.employee_id = e.employee_id
                WHERE e.employee_id IS NULL
            """,

            "SalaryRecord -> CompensationBand": """
                SELECT COUNT(*) FROM salary_records s
                LEFT JOIN compensation_bands b ON s.band_id = b.band_id
                WHERE b.band_id IS NULL
            """,

            "PerformanceEvidence -> Employee": """
                SELECT COUNT(*) FROM performance_evidence p
                LEFT JOIN employees e ON p.employee_id = e.employee_id
                WHERE e.employee_id IS NULL
            """,

            "Tenure -> Employee": """
                SELECT COUNT(*) FROM tenures t
                LEFT JOIN employees e ON t.employee_id = e.employee_id
                WHERE e.employee_id IS NULL
            """,

            "Promotion -> Employee": """
                SELECT COUNT(*) FROM promotions p
                LEFT JOIN employees e ON p.employee_id = e.employee_id
                WHERE e.employee_id IS NULL
            """,

            "Promotion -> Previous Role": """
                SELECT COUNT(*) FROM promotions p
                LEFT JOIN roles r ON p.previous_role_id = r.role_id
                WHERE r.role_id IS NULL
            """,

            "Promotion -> New Role": """
                SELECT COUNT(*) FROM promotions p
                LEFT JOIN roles r ON p.new_role_id = r.role_id
                WHERE r.role_id IS NULL
            """,

            "Promotion -> Previous Level": """
                SELECT COUNT(*) FROM promotions p
                LEFT JOIN levels l ON p.previous_level_id = l.level_id
                WHERE l.level_id IS NULL
            """,

            "Promotion -> New Level": """
                SELECT COUNT(*) FROM promotions p
                LEFT JOIN levels l ON p.new_level_id = l.level_id
                WHERE l.level_id IS NULL
            """,

            "AdjustmentProposal -> Employee": """
                SELECT COUNT(*) FROM adjustment_proposals a
                LEFT JOIN employees e ON a.employee_id = e.employee_id
                WHERE e.employee_id IS NULL
            """,

            "AdjustmentProposal -> SalaryRecord": """
                SELECT COUNT(*) FROM adjustment_proposals a
                LEFT JOIN salary_records s ON a.current_salary_id = s.salary_id
                WHERE s.salary_id IS NULL
            """,

            "ProposalHistory -> AdjustmentProposal": """
                SELECT COUNT(*) FROM proposal_history h
                LEFT JOIN adjustment_proposals a ON h.proposal_id = a.proposal_id
                WHERE a.proposal_id IS NULL
            """
        }

        all_passed = True

        for name, query in checks.items():
            result = db.session.execute(text(query)).scalar()

            status = "PASS" if result == 0 else "FAIL"

            print(f"{name}: {status} | Invalid references: {result}")

            if result != 0:
                all_passed = False

        print("\n========== DATABASE COUNTS ==========")

        tables = [
            "employees",
            "salary_records",
            "performance_evidence",
            "tenures",
            "promotions",
            "adjustment_proposals",
            "proposal_history"
        ]

        for table in tables:
            count = db.session.execute(
                text(f"SELECT COUNT(*) FROM {table}")
            ).scalar()

            print(f"{table}: {count}")

        print("\n======================================")

        if all_passed:
            print("SUCCESS: ALL RELATIONSHIP CHECKS PASSED!")
        else:
            print("WARNING: INVALID REFERENCES FOUND!")

        return all_passed


if __name__ == "__main__":
    verify_relationships()
