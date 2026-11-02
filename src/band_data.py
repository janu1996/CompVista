
"""
CompVista - Compensation Band Master Data Generator

40 Roles x 5 Levels x 8 Locations = 1,600 Bands
Uses the separate upgrade testing database.
"""

import os
import sys
from datetime import date
from decimal import Decimal

# Always use testing database
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
from models import Role, Level, Location, CompensationBand


# Annual midpoint salary reference in INR
BASE_SALARIES = {
    "Intern": Decimal("300000"),
    "Junior": Decimal("500000"),
    "Mid-Level": Decimal("900000"),
    "Senior": Decimal("1500000"),
    "Lead": Decimal("2200000"),
}

# Documented synthetic FX assumption.
# 1 GBP = 105 INR
INR_PER_GBP = Decimal("105.00")

CENT = Decimal("0.01")

EFFECTIVE_FROM = date(2023, 1, 1)
EFFECTIVE_TO = None


def generate_bands():

    with app.app_context():

        database_uri = app.config["SQLALCHEMY_DATABASE_URI"]

        if "compvista_upgrade_test.db" not in database_uri:
            raise RuntimeError(
                "Safety check failed: testing database not selected."
            )

        roles = Role.query.order_by(Role.role_id).all()

        levels = Level.query.order_by(
            Level.level_rank
        ).all()

        locations = Location.query.order_by(
            Location.location_id
        ).all()

        if len(roles) != 40:
            raise RuntimeError(
                f"Expected 40 roles, found {len(roles)}."
            )

        if len(levels) != 5:
            raise RuntimeError(
                f"Expected 5 levels, found {len(levels)}."
            )

        if len(locations) != 8:
            raise RuntimeError(
                f"Expected 8 locations, found {len(locations)}."
            )

        existing_bands = {
            band.band_id
            for band in CompensationBand.query.all()
        }

        generated = 0
        skipped = 0

        for role in roles:

            role_multiplier = Decimal(
                str(0.90 + ((role.role_id - 1) % 5) * 0.05)
            )

            for level in levels:

                base_salary = BASE_SALARIES.get(
                    level.level_name
                )

                if base_salary is None:
                    raise RuntimeError(
                        f"Missing salary reference for {level.level_name}"
                    )

                for location in locations:

                    # Salary band calculation in INR
                    midpoint_inr = (
                        base_salary
                        * role_multiplier
                        * Decimal(str(location.cost_of_living_index))
                    )

                    # Convert band values into location currency
                    if location.currency_code == "GBP":
                        midpoint = midpoint_inr / INR_PER_GBP
                    elif location.currency_code == "INR":
                        midpoint = midpoint_inr
                    else:
                        raise RuntimeError(
                            f"Unsupported currency: {location.currency_code}"
                        )

                    midpoint = midpoint.quantize(CENT)

                    minimum = (
                        midpoint * Decimal("0.80")
                    ).quantize(CENT)

                    maximum = (
                        midpoint * Decimal("1.20")
                    ).quantize(CENT)

                    # Required deterministic naming convention
                    band_id = (
                        f"BAND-{role.role_id:03d}-"
                        f"{level.level_id:03d}-"
                        f"{location.location_id:03d}-2026"
                    )

                    if band_id in existing_bands:
                        skipped += 1
                        continue

                    band = CompensationBand(
                        band_id=band_id,
                        role_id=role.role_id,
                        level_id=level.level_id,
                        location_id=location.location_id,
                        min_salary=minimum,
                        midpoint_salary=midpoint,
                        max_salary=maximum,
                        currency_code=location.currency_code,
                        effective_from=EFFECTIVE_FROM,
                        effective_to=EFFECTIVE_TO
                    )

                    db.session.add(band)
                    existing_bands.add(band_id)
                    generated += 1

        try:
            db.session.commit()

        except Exception:
            db.session.rollback()
            raise

        total = CompensationBand.query.count()

        print("\nCOMPVISTA COMPENSATION BANDS")
        print("============================")
        print("New bands generated:", generated)
        print("Existing bands skipped:", skipped)
        print("Total bands:", total)
        print("Expected bands:", 1600)

        if total != 1600:
            raise RuntimeError(
                f"Expected 1600 bands, found {total}."
            )

        print("\nCompensation band generation completed!")


if __name__ == "__main__":
    generate_bands()
