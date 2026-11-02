
import os
import sys

# Always use the upgrade testing database
os.environ["COMPVISTA_DB_PATH"] = (
    "backend/compvista_upgrade_test.db"
)

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

BACKEND_PATH = os.path.join(PROJECT_ROOT, "backend")

if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

from app import app
from extensions import db
from models import CompensationBand, SalaryRecord


def migrate_bands():

    with app.app_context():

        database_uri = app.config["SQLALCHEMY_DATABASE_URI"]

        if "compvista_upgrade_test.db" not in database_uri:
            raise RuntimeError("Wrong database selected!")

        try:
            bands = CompensationBand.query.all()

            old_bands = [
                b for b in bands
                if not b.band_id.endswith("-2026")
            ]

            new_bands = {
                (b.role_id, b.level_id, b.location_id): b
                for b in bands
                if b.band_id.endswith("-2026")
            }

            print("Old bands found:", len(old_bands))
            print("New bands found:", len(new_bands))

            if len(old_bands) != 800 or len(new_bands) != 1600:
                raise RuntimeError(
                    "Unexpected band counts. Migration stopped."
                )

            migrated_records = 0
            unused_old_bands = []

            for old_band in old_bands:

                key = (
                    old_band.role_id,
                    old_band.level_id,
                    old_band.location_id
                )

                new_band = new_bands.get(key)

                if new_band is None:
                    raise RuntimeError(
                        f"No matching new band for {old_band.band_id}"
                    )

                # Move salary records to matching new band.
                affected = SalaryRecord.query.filter_by(
                    band_id=old_band.band_id
                ).update(
                    {"band_id": new_band.band_id},
                    synchronize_session=False
                )

                migrated_records += affected

                # Verify no salary records still reference old band.
                remaining = SalaryRecord.query.filter_by(
                    band_id=old_band.band_id
                ).count()

                if remaining != 0:
                    raise RuntimeError(
                        f"Old band still referenced: {old_band.band_id}"
                    )

                unused_old_bands.append(old_band)

            # Delete only after all salary references are migrated.
            for old_band in unused_old_bands:
                db.session.delete(old_band)

            db.session.flush()

            # Final checks before commit.
            final_band_count = CompensationBand.query.count()
            final_salary_count = SalaryRecord.query.count()

            remaining_old = [
                b.band_id
                for b in CompensationBand.query.all()
                if not b.band_id.endswith("-2026")
            ]

            if final_band_count != 1600:
                raise RuntimeError(
                    f"Expected 1600 bands, found {final_band_count}"
                )

            if remaining_old:
                raise RuntimeError(
                    f"Old bands remain: {remaining_old[:5]}"
                )

            db.session.commit()

            print("\nBAND MIGRATION SUCCESSFUL")
            print("=========================")
            print("Salary references updated:", migrated_records)
            print("Old bands removed:", len(unused_old_bands))
            print("Final compensation bands:", final_band_count)
            print("Salary records preserved:", final_salary_count)

        except Exception:
            db.session.rollback()
            print("\nMigration failed. Transaction rolled back.")
            raise


if __name__ == "__main__":
    migrate_bands()
