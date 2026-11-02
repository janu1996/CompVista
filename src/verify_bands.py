
import os
import sys
from collections import Counter

# Use the separate upgrade test database
os.environ["COMPVISTA_DB_PATH"] = "backend/compvista_upgrade_test.db"

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_PATH = os.path.join(PROJECT_ROOT, "backend")

if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

from app import app
from models import Role, Level, Location, CompensationBand


def verify_bands():
    with app.app_context():

        database_uri = app.config["SQLALCHEMY_DATABASE_URI"]

        if "compvista_upgrade_test.db" not in database_uri:
            raise RuntimeError("Wrong database selected!")

        roles = Role.query.all()
        levels = Level.query.all()
        locations = Location.query.all()
        bands = CompensationBand.query.all()

        print("\n========== COMPVISTA BAND VALIDATION ==========")

        print("Total roles:", len(roles))
        print("Total levels:", len(levels))
        print("Total locations:", len(locations))
        print("Total compensation bands:", len(bands))

        expected_combinations = {
            (role.role_id, level.level_id, location.location_id)
            for role in roles
            for level in levels
            for location in locations
        }

        actual_combinations = [
            (band.role_id, band.level_id, band.location_id)
            for band in bands
        ]

        counts = Counter(actual_combinations)

        duplicates = [
            combination
            for combination, count in counts.items()
            if count > 1
        ]

        actual_set = set(actual_combinations)
        missing = expected_combinations - actual_set
        unexpected = actual_set - expected_combinations

        invalid_ranges = [
            band.band_id
            for band in bands
            if not (
                band.min_salary < band.midpoint_salary < band.max_salary
            )
        ]

        invalid_dates = [
            band.band_id
            for band in bands
            if band.effective_to is not None
            and band.effective_from > band.effective_to
        ]

        print("\n========== VALIDATION RESULTS ==========")

        print("Expected combinations:", len(expected_combinations))
        print("Actual unique combinations:", len(actual_set))
        print("Duplicate combinations:", len(duplicates))
        print("Missing combinations:", len(missing))
        print("Unexpected combinations:", len(unexpected))
        print("Invalid salary ranges:", len(invalid_ranges))
        print("Invalid effective dates:", len(invalid_dates))

        if duplicates:
            print("\nDuplicate examples:", duplicates[:5])

        if missing:
            print("\nMissing examples:", list(missing)[:5])

        if unexpected:
            print("\nUnexpected examples:", list(unexpected)[:5])

        if invalid_ranges:
            print("\nInvalid salary band IDs:", invalid_ranges[:5])

        if invalid_dates:
            print("\nInvalid date band IDs:", invalid_dates[:5])

        success = (
            len(roles) == 40
            and len(levels) == 5
            and len(locations) == 8
            and len(bands) == 1600
            and len(actual_set) == 1600
            and len(duplicates) == 0
            and len(missing) == 0
            and len(unexpected) == 0
            and len(invalid_ranges) == 0
            and len(invalid_dates) == 0
        )

        print("\n========================================")

        if success:
            print("SUCCESS: ALL BAND VALIDATIONS PASSED!")
        else:
            print("VALIDATION FAILED: Please check the results.")

        return success


if __name__ == "__main__":
    verify_bands()
