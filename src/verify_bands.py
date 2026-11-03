
import os
import sqlite3
import sys
from pathlib import Path
from collections import Counter

DB_PATH = os.environ.get(
    "COMPVISTA_DB_PATH",
    "backend/compvista_backup.db"
)

db_file = Path(DB_PATH).resolve()

if not db_file.exists():
    raise FileNotFoundError(f"Database not found: {db_file}")

connection = sqlite3.connect(
    db_file.as_uri() + "?mode=ro",
    uri=True
)
cursor = connection.cursor()

success = False

try:
    print("\n========== COMPVISTA BAND VALIDATION ==========")
    print("Database:", db_file.name)

    roles = cursor.execute(
        "SELECT role_id FROM roles"
    ).fetchall()

    levels = cursor.execute(
        "SELECT level_id FROM levels"
    ).fetchall()

    locations = cursor.execute(
        "SELECT location_id FROM locations"
    ).fetchall()

    bands = cursor.execute("""
        SELECT band_id, role_id, level_id, location_id,
               min_salary, midpoint_salary, max_salary,
               effective_from, effective_to, currency_code
        FROM compensation_bands
    """).fetchall()

    print("Total roles:", len(roles))
    print("Total levels:", len(levels))
    print("Total locations:", len(locations))
    print("Total compensation bands:", len(bands))

    expected = {
        (r[0], l[0], loc[0])
        for r in roles
        for l in levels
        for loc in locations
    }

    actual = [
        (b[1], b[2], b[3])
        for b in bands
    ]

    counts = Counter(actual)

    duplicates = [
        combo for combo, count in counts.items()
        if count > 1
    ]

    actual_set = set(actual)
    missing = expected - actual_set
    unexpected = actual_set - expected

    invalid_ranges = [
        b[0] for b in bands
        if not (0 < b[4] < b[5] < b[6])
    ]

    invalid_dates = [
        b[0] for b in bands
        if b[8] is not None and b[8] <= b[7]
    ]

    missing_currency = [
        b[0] for b in bands
        if not b[9] or not b[9].strip()
    ]

    print("\n========== VALIDATION RESULTS ==========")
    print("Expected combinations:", len(expected))
    print("Actual unique combinations:", len(actual_set))
    print("Duplicate combinations:", len(duplicates))
    print("Missing combinations:", len(missing))
    print("Unexpected combinations:", len(unexpected))
    print("Invalid salary ranges:", len(invalid_ranges))
    print("Invalid effective dates:", len(invalid_dates))
    print("Missing currencies:", len(missing_currency))

    if duplicates:
        print("Duplicate examples:", duplicates[:5])

    if missing:
        print("Missing examples:", list(missing)[:5])

    if invalid_ranges:
        print("Invalid salary band IDs:", invalid_ranges[:5])

    if invalid_dates:
        print("Invalid date band IDs:", invalid_dates[:5])

    success = (
        len(expected) > 0
        and len(bands) == len(expected)
        and len(actual_set) == len(expected)
        and len(duplicates) == 0
        and len(missing) == 0
        and len(unexpected) == 0
        and len(invalid_ranges) == 0
        and len(invalid_dates) == 0
        and len(missing_currency) == 0
    )

    print("\n========================================")

    if success:
        print("SUCCESS: ALL BAND VALIDATIONS PASSED!")
    else:
        print("VALIDATION FAILED: Please investigate.")

finally:
    cursor.close()
    connection.close()

if not success:
    sys.exit(1)
