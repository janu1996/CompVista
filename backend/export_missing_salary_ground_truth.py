import csv
import json
from pathlib import Path

from datetime import date
from app import app
from models import Employee, SalaryRecord

AS_OF_DATE = date(2026, 10, 26)

OUTPUT_DIR = Path("../data")
CSV_DIR = OUTPUT_DIR / "csv"
JSON_DIR = OUTPUT_DIR / "json"

CSV_DIR.mkdir(parents=True, exist_ok=True)
JSON_DIR.mkdir(parents=True, exist_ok=True)

ground_truth = []

with app.app_context():
    employees = Employee.query.filter_by(
        employment_status="ACTIVE"
    ).all()

    for employee in employees:
        active_salary = SalaryRecord.query.filter(
            SalaryRecord.employee_id == employee.employee_id,
            SalaryRecord.effective_from <= AS_OF_DATE,
            (
                SalaryRecord.effective_to.is_(None)
                | (SalaryRecord.effective_to > AS_OF_DATE)
            )
        ).count()

        if active_salary == 0:
            ground_truth.append({
                "scenario_id": f"GT-MISSING-{employee.employee_id}",
                "employee_id": employee.employee_id,
                "expected_issue": "MISSING_SALARY",
                "severity": "HIGH",
                "expected_detection": "missing_salary",
                "analysis_date": AS_OF_DATE.isoformat(),
                "description": (
                    "Active employee has no applicable salary "
                    "record on the analysis date."
                )
            })

fields = [
    "scenario_id",
    "employee_id",
    "expected_issue",
    "severity",
    "expected_detection",
    "analysis_date",
    "description"
]

csv_path = CSV_DIR / "ground_truth.csv"
json_path = JSON_DIR / "ground_truth.json"

with csv_path.open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=fields)
    writer.writeheader()
    writer.writerows(ground_truth)

with json_path.open("w", encoding="utf-8") as file:
    json.dump(ground_truth, file, indent=4)

print("Ground-truth records:", len(ground_truth))
print("CSV:", csv_path)
print("JSON:", json_path)
print("GROUND TRUTH EXPORT: SUCCESS")
