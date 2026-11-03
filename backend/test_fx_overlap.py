from datetime import date
from decimal import Decimal

from app import app
from extensions import db
from models import FXRate
from services.fx_service import get_historical_fx_rate

with app.app_context():
    test_rate = FXRate(
        from_currency="GBP",
        to_currency="INR",
        rate=Decimal("111.000000"),
        effective_from=date(2025, 1, 1),
        effective_to=None,
        source="OVERLAP_TEST"
    )

    try:
        db.session.add(test_rate)
        db.session.commit()

        try:
            get_historical_fx_rate(
                "GBP", "INR", date(2025, 6, 15)
            )
        except ValueError as error:
            print("Overlap protection: PASS")
            print("Message:", error)
        else:
            raise AssertionError("Overlapping rates were not rejected")

    finally:
        db.session.rollback()

        test_row = FXRate.query.filter_by(
            source="OVERLAP_TEST"
        ).first()

        if test_row:
            db.session.delete(test_row)
            db.session.commit()

        print("Temporary test rate cleaned up.")

    print("OVERLAP TEST COMPLETED")
