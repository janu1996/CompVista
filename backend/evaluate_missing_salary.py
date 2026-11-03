import csv
import json
from pathlib import Path

from datetime import date
from app import app
from services.compensation_analysis import analyze_compensation

csv_path = Path("../data/csv/ground_truth.csv")
json_path = Path("../data/json/ground_truth.json")

with csv_path.open(encoding="utf-8") as file:
    csv_rows = list(csv.DictReader(file))

with json_path.open(encoding="utf-8") as file:
    json_rows = json.load(file)

with app.app_context():
    report = analyze_compensation(date(2026, 10, 26))
    detected_count = report["summary"]["data_quality_issues"]["missing_salary"]

expected_ids = {row["employee_id"] for row in csv_rows}
json_ids = {row["employee_id"] for row in json_rows}

print("CSV records:", len(csv_rows))
print("JSON records:", len(json_rows))
print("CSV/JSON IDs match:", expected_ids == json_ids)
print("Expected missing salary:", len(expected_ids))
print("Detector missing salary:", detected_count)

assert expected_ids == json_ids
assert len(expected_ids) == detected_count

print("MISSING SALARY GROUND-TRUTH EVALUATION: PASS")
