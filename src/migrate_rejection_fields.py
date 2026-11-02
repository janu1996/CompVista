
import os
import sys

os.environ["COMPVISTA_DB_PATH"] = "backend/compvista_upgrade_test.db"

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_PATH = os.path.join(PROJECT_ROOT, "backend")

if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

from app import app
from extensions import db
from sqlalchemy import text, inspect


def migrate_rejection_fields():

    with app.app_context():

        database_uri = app.config["SQLALCHEMY_DATABASE_URI"]

        if "compvista_upgrade_test.db" not in database_uri:
            raise RuntimeError("Wrong database selected!")

        try:
            inspector = inspect(db.engine)

            columns = [
                column["name"]
                for column in inspector.get_columns(
                    "adjustment_proposals"
                )
            ]

            print("\nREJECTION FIELD MIGRATION")
            print("=========================")

            if "rejected_by" not in columns:
                db.session.execute(text("""
                    ALTER TABLE adjustment_proposals
                    ADD COLUMN rejected_by VARCHAR(100)
                """))
                print("Added rejected_by column")
            else:
                print("rejected_by already exists")

            if "rejected_at" not in columns:
                db.session.execute(text("""
                    ALTER TABLE adjustment_proposals
                    ADD COLUMN rejected_at DATETIME
                """))
                print("Added rejected_at column")
            else:
                print("rejected_at already exists")

            # Preserve rejection details using the existing
            # proposal history and audit log.
            db.session.execute(text("""
                UPDATE adjustment_proposals
                SET
                    rejected_by = (
                        SELECT h.changed_by
                        FROM proposal_history h
                        WHERE h.proposal_id =
                              adjustment_proposals.proposal_id
                          AND h.new_status = 'REJECTED'
                        ORDER BY h.changed_at DESC, h.history_id DESC
                        LIMIT 1
                    ),
                    rejected_at = (
                        SELECT h.changed_at
                        FROM proposal_history h
                        WHERE h.proposal_id =
                              adjustment_proposals.proposal_id
                          AND h.new_status = 'REJECTED'
                        ORDER BY h.changed_at DESC, h.history_id DESC
                        LIMIT 1
                    )
                WHERE status = 'REJECTED'
            """))

            db.session.commit()

            result = db.session.execute(text("""
                SELECT
                    proposal_id,
                    status,
                    rejected_by,
                    rejected_at
                FROM adjustment_proposals
                WHERE status = 'REJECTED'
            """)).fetchall()

            print("\nRejected proposal verification:")

            for row in result:
                print(row)

            if not result:
                raise RuntimeError(
                    "Expected rejected proposal was not found."
                )

            if any(not row[2] or not row[3] for row in result):
                raise RuntimeError(
                    "Some rejection details could not be recovered."
                )

            print("\nMIGRATION SUCCESSFUL")

        except Exception:
            db.session.rollback()
            print("\nMigration failed. Transaction rolled back.")
            raise


if __name__ == "__main__":
    migrate_rejection_fields()
