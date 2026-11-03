from datetime import date
from decimal import Decimal
from app import app
from extensions import db
from models import SalaryRecord, Employee, CompensationBand
from services.compensation_analysis import analyze_compensation

TARGET = "EMP-000204"
PEERS = ["EMP-000666", "EMP-001991", "EMP-003712", "EMP-004729"]
AS_OF_DATE = date(2026, 10, 26)
TEST_SALARY = Decimal("14000.00")

with app.app_context():
    ids = [TARGET] + PEERS
    records = {}

    for employee_id in ids:
        employee = db.session.get(Employee, employee_id)
        salary = SalaryRecord.query.filter(
            SalaryRecord.employee_id == employee_id,
            SalaryRecord.effective_from <= AS_OF_DATE,
            (SalaryRecord.effective_to.is_(None) |
             (SalaryRecord.effective_to > AS_OF_DATE))
        ).first()

        if employee is None or salary is None:
            raise RuntimeError(f"Missing employee or active salary: {employee_id}")

        records[employee_id] = (employee, salary)

    # Confirm all five employees belong to the same comparison group.
    target_employee, target_salary = records[TARGET]
    for employee_id in PEERS:
        employee, salary = records[employee_id]
        same_group = (
            employee.role_id == target_employee.role_id
            and employee.level_id == target_employee.level_id
            and employee.location_id == target_employee.location_id
            and salary.currency_code == target_salary.currency_code
        )
        if not same_group:
            raise RuntimeError(f"{employee_id} is not in the target comparison group.")

        band = db.session.get(CompensationBand, salary.band_id)
        if band is None or not (band.min_salary <= TEST_SALARY <= band.max_salary):
            raise RuntimeError(f"?14000 is outside the valid band for {employee_id}.")

    originals = {
        employee_id: salary.base_salary
        for employee_id, (_, salary) in records.items()
    }

    try:
        for employee_id in PEERS:
            records[employee_id][1].base_salary = TEST_SALARY
        db.session.commit()

        report = analyze_compensation(AS_OF_DATE)
        result = next(
            row for row in report["results"]
            if row["employee_id"] == TARGET
        )
        issue_types = [
            flag["type"] for flag in result["potential_issues"]
        ]

        print("Target salary:", target_salary.base_salary)
        print("Peer test salaries:", TEST_SALARY)
        print("Detected issues:", issue_types)

        assert "PEER_PAY_GAP" in issue_types, "Peer-pay-gap flag was not detected."
        assert "BELOW_BAND_MINIMUM" not in issue_types, "Unexpected below-band flag."

        print("PEER-PAY-GAP SCENARIO: PASS")

    finally:
        for employee_id, (_, salary) in records.items():
            salary.base_salary = originals[employee_id]
        db.session.commit()
        print("All original salaries restored.")
