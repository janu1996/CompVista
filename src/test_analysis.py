import os
import sys
import json

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

BACKEND_PATH = os.path.join(PROJECT_ROOT, "backend")

sys.path.insert(0, BACKEND_PATH)

from app import app
from services.compensation_analysis import analyze_compensation


with app.app_context():

    print("\nCOMPVISTA COMPENSATION ANALYSIS")
    print("=" * 40)

    report = analyze_compensation()

    summary = report["summary"]

    print("\nANALYSIS SUMMARY")
    print("-" * 40)

    for key, value in summary.items():
        print(f"{key}: {value}")

    print("\nSAMPLE EMPLOYEE RESULTS")
    print("-" * 40)

    for employee in report["results"][:5]:

        print("\nEmployee:", employee["employee_name"])
        print("Employee ID:", employee["employee_id"])
        print("Salary:", employee["actual_salary"])
        print("FTE:", employee["fte"])
        print("Compa Ratio:", employee["compa_ratio"], "%")
        print("Band Position:", employee["band_position"], "%")
        print("Peer Median:", employee["peer_median_salary"])
        print("HR Review Required:", employee["requires_hr_review"])

        if employee["potential_issues"]:
            print("Potential Issues:")

            for issue in employee["potential_issues"]:
                print("-", issue["type"], ":", issue["message"])

    print("\nAnalysis testing completed!")