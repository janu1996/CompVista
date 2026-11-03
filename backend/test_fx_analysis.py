from datetime import date
from decimal import Decimal

from app import app
from services.compensation_analysis import analyze_compensation

with app.app_context():
    report = analyze_compensation(date(2026, 10, 26))

    summary = report["summary"]
    results = report["results"]

    print("SUMMARY:", summary)
    print("RESULT COUNT:", len(results))

    assert summary["reporting_currency"] == "INR"

    gbp_rows = [
        row for row in results
        if row["currency_code"] == "GBP"
    ]

    inr_rows = [
        row for row in results
        if row["currency_code"] == "INR"
    ]

    assert gbp_rows, "No GBP analysis rows found"
    assert inr_rows, "No INR analysis rows found"

    sample = gbp_rows[0]

    assert sample["normalized_salary_inr"] == (
        sample["normalized_salary"] * Decimal("110")
    ).quantize(Decimal("0.01"))

    assert sample["reporting_currency"] == "INR"
    assert sample["fx_effective_date"] == "2026-10-26"

    print("GBP sample:", {
        "original_salary": sample["normalized_salary"],
        "currency": sample["currency_code"],
        "salary_inr": sample["normalized_salary_inr"],
        "fx_rate": sample["fx_rate"],
        "compa_ratio": sample["compa_ratio"],
    })

    print("INR sample:", {
        "original_salary": inr_rows[0]["normalized_salary"],
        "salary_inr": inr_rows[0]["normalized_salary_inr"],
        "fx_rate": inr_rows[0]["fx_rate"],
    })

    print("FX ANALYSIS INTEGRATION: PASS")
