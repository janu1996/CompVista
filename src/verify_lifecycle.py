
import os
import sys

# Use isolated workflow test database
os.environ["COMPVISTA_DB_PATH"] = (
    "backend/compvista_workflow_test.db"
)

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

BACKEND_PATH = os.path.join(
    PROJECT_ROOT,
    "backend"
)

if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

from app import app
from sqlalchemy import text


def verify_lifecycle():

    with app.app_context():

        database_uri = app.config["SQLALCHEMY_DATABASE_URI"]

        if "compvista_workflow_test.db" not in database_uri:
            raise RuntimeError("Wrong database selected!")

        print("\n========== PROPOSAL LIFECYCLE VALIDATION ==========")
        print("Database:", database_uri)

        checks = {

            "Invalid proposal status": """
                SELECT COUNT(*)
                FROM adjustment_proposals
                WHERE status NOT IN (
                    'DRAFT',
                    'SUBMITTED',
                    'APPROVED',
                    'REJECTED',
                    'APPLIED'
                )
            """,

            "Approved without approver": """
                SELECT COUNT(*)
                FROM adjustment_proposals
                WHERE status IN ('APPROVED', 'APPLIED')
                AND (
                    approved_by IS NULL
                    OR TRIM(approved_by) = ''
                    OR approved_at IS NULL
                )
            """,

            "Rejected without rejection details": """
                SELECT COUNT(*)
                FROM adjustment_proposals
                WHERE status = 'REJECTED'
                AND (
                    rejected_by IS NULL
                    OR TRIM(rejected_by) = ''
                    OR rejected_at IS NULL
                )
            """,

            "Applied without applied timestamp": """
                SELECT COUNT(*)
                FROM adjustment_proposals
                WHERE status = 'APPLIED'
                AND applied_at IS NULL
            """,

            "Applied before approval": """
                SELECT COUNT(*)
                FROM adjustment_proposals
                WHERE status = 'APPLIED'
                AND (
                    approved_at IS NULL
                    OR applied_at < approved_at
                )
            """,

            "Non-positive proposed salary": """
                SELECT COUNT(*)
                FROM adjustment_proposals
                WHERE proposed_salary <= 0
            """,

            "Missing proposal reason": """
                SELECT COUNT(*)
                FROM adjustment_proposals
                WHERE reason IS NULL
                OR TRIM(reason) = ''
            """,

            "Missing proposal creator": """
                SELECT COUNT(*)
                FROM adjustment_proposals
                WHERE proposed_by IS NULL
                OR TRIM(proposed_by) = ''
            """,

            "Applied proposal without matching salary record": """
                SELECT COUNT(*)
                FROM adjustment_proposals p
                WHERE p.status = 'APPLIED'
                AND NOT EXISTS (
                    SELECT 1
                    FROM salary_records s
                    WHERE s.employee_id = p.employee_id
                    AND s.change_reason =
                        'Approved adjustment: ' || p.proposal_id
                    AND s.effective_from = DATE(p.applied_at)
                )
            """,

            "Applied proposal without complete history": """
                SELECT COUNT(*)
                FROM adjustment_proposals p
                WHERE p.status = 'APPLIED'
                AND (
                    SELECT COUNT(*)
                    FROM proposal_history h
                    WHERE h.proposal_id = p.proposal_id
                    AND h.new_status = 'APPLIED'
                ) = 0
            """,

            "Applied proposal without audit record": """
                SELECT COUNT(*)
                FROM adjustment_proposals p
                WHERE p.status = 'APPLIED'
                AND NOT EXISTS (
                    SELECT 1
                    FROM audit_logs a
                    WHERE a.entity_id = p.proposal_id
                    AND a.action = 'APPLY'
                )
            """
        }

        all_passed = True

        print("\n========== VALIDATION RESULTS ==========")

        for name, query in checks.items():

            result = app.extensions[
                "sqlalchemy"
            ].session.execute(
                text(query)
            ).scalar()

            status = "PASS" if result == 0 else "CHECK"

            print(
                f"{name}: {status} | Records found: {result}"
            )

            if result != 0:
                all_passed = False

        print("\n========== PROPOSAL STATUS SUMMARY ==========")

        status_query = text("""
            SELECT status, COUNT(*)
            FROM adjustment_proposals
            GROUP BY status
            ORDER BY status
        """)

        rows = app.extensions[
            "sqlalchemy"
        ].session.execute(
            status_query
        ).fetchall()

        for status, count in rows:
            print(f"{status}: {count}")

        print("\n========== TEST PROPOSAL DETAILS ==========")

        test_proposals = [
            "PROP-P-000080--000080-2026",
            "PROP-P-000216--000216-2026"
        ]

        for proposal_id in test_proposals:

            row = app.extensions[
                "sqlalchemy"
            ].session.execute(
                text("""
                    SELECT proposal_id, status,
                           approved_by, rejected_by
                    FROM adjustment_proposals
                    WHERE proposal_id = :proposal_id
                """),
                {"proposal_id": proposal_id}
            ).fetchone()

            if row:
                print(
                    f"Proposal: {row[0]} | "
                    f"Status: {row[1]} | "
                    f"Approved by: {row[2]} | "
                    f"Rejected by: {row[3]}"
                )

        print("\n==============================================")

        if all_passed:
            print("SUCCESS: ALL LIFECYCLE CHECKS PASSED!")
        else:
            print(
                "REVIEW REQUIRED: "
                "Some lifecycle conditions need investigation."
            )

        return all_passed


if __name__ == "__main__":
    verify_lifecycle()
