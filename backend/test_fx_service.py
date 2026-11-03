from datetime import date
from decimal import Decimal

from app import app
from services.fx_service import (
    get_historical_fx_rate,
    convert_to_inr
)

with app.app_context():

    rate = get_historical_fx_rate(
        "GBP", "INR", date(2025, 6, 15)
    )
    print("GBP to INR rate:", rate)
    assert rate == Decimal("110.000000")

    result = convert_to_inr(
        Decimal("1000"),
        "GBP",
        date(2025, 6, 15)
    )
    print("\nGBP conversion:", result)
    assert result["converted_amount"] == Decimal("110000.00")

    inr_result = convert_to_inr(
        Decimal("5000"),
        "INR",
        date(2025, 6, 15)
    )
    print("\nINR conversion:", inr_result)
    assert inr_result["converted_amount"] == Decimal("5000.00")

    try:
        get_historical_fx_rate(
            "USD", "INR", date(2025, 6, 15)
        )
    except ValueError:
        print("\nMissing-rate validation: PASS")
    else:
        raise AssertionError("Missing FX rate was not rejected")

    print("\nALL FX SERVICE CHECKS PASSED")
