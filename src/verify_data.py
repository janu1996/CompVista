
import os
import sys

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

sys.path.insert(
    0,
    os.path.join(PROJECT_ROOT, "backend")
)

from app import app
from models import Employee, SalaryRecord, CompensationBand

with app.app_context():

    print("\nCOMPVISTA DATA VERIFICATION")
    print("============================")

    print("Employees:", Employee.query.count())
    print("Salary Records:", SalaryRecord.query.count())
    print("Compensation Bands:", CompensationBand.query.count())

    print("\nSalary Records by Currency:")

    records = SalaryRecord.query.all()

    inr_count = sum(
        1 for record in records
        if record.currency_code == "INR"
    )

    gbp_count = sum(
        1 for record in records
        if record.currency_code == "GBP"
    )

    print("INR Records:", inr_count)
    print("GBP Records:", gbp_count)

    print("\nDate Validation:")

    invalid_dates = SalaryRecord.query.filter(
        SalaryRecord.effective_to.isnot(None),
        SalaryRecord.effective_to <= SalaryRecord.effective_from
    ).count()

    print("Invalid Date Records:", invalid_dates)

    print("\nFTE Validation:")

    invalid_fte = SalaryRecord.query.filter(
        (SalaryRecord.fte <= 0) |
        (SalaryRecord.fte > 1)
    ).count()

    print("Invalid FTE Records:", invalid_fte)

    print("\nSalary Validation:")

    invalid_salary = SalaryRecord.query.filter(
        SalaryRecord.base_salary <= 0
    ).count()

    print("Invalid Salary Records:", invalid_salary)

    print("\nVerification Completed!")
