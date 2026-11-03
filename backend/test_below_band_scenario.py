from datetime import date
from decimal import Decimal

from app import app
from extensions import db
from models import SalaryRecord
from services.compensation_analysis import analyze_compensation

EMPLOYEE_ID = "EMP-000204"
AS_OF_DATE = date(2026, 10, 26)

with app.app_context():
    salary = SalaryRecord.query.filter(
        SalaryRecord.employee_id == EMPLOYEE_ID,
        SalaryRecord.effective_from <= AS_OF_DATE,
        (
            SalaryRecord.effective_to.is_(None)
            | (SalaryRecord.effective_to > AS_OF_DATE)
        )
    ).first()

    if salary is None:
        raise RuntimeError("Active salary record not found.")

    original_salary = salary.base_salary

    try:
        salary.base_salary = Decimal("10000.00")
        db.session.commit()

        report = analyze_compensation(AS_OF_DATE)

        result = next(
            row for row in report["results"]
            if row["employee_id"] == EMPLOYEE_ID
        )

        detected = any(
            flag["type"] == "BELOW_BAND_MINIMUM"
            for flag in result["potential_issues"]
        )

        print("Test salary:", result["normalized_salary"])
        print("Band minimum:", result["band_minimum"])
        print("Below-band detected:", detected)

        assert detected, "Below-band detector failed!"

        print("BELOW-BAND SCENARIO: PASS")

    finally:
        salary.base_salary = original_salary
        db.session.commit()
        print("Original salary restored:", original_salary)
