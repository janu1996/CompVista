from datetime import date
from decimal import Decimal

from extensions import db
from models import Employee, SalaryRecord
from services.compensation_analysis import analyze_compensation


def test_analysis_returns_expected_structure():
    report = analyze_compensation()

    assert "summary" in report
    assert "results" in report
    assert isinstance(report["summary"], dict)
    assert isinstance(report["results"], list)


def test_analysis_summary_has_required_fields():
    report = analyze_compensation()
    summary = report["summary"]

    expected_fields = [
        "employees_analyzed",
        "employees_flagged",
        "employees_without_flags",
        "below_band_minimum",
        "low_compa_ratio",
        "peer_pay_gap",
    ]

    for field in expected_fields:
        assert field in summary


def test_analysis_with_as_of_date():
    report = analyze_compensation(as_of_date=date(2026, 1, 1))

    assert isinstance(report, dict)
    assert "summary" in report
    assert "results" in report


def test_empty_database_returns_zero_employees():
    report = analyze_compensation()
    summary = report["summary"]

    assert summary["employees_analyzed"] == 0
    assert summary["employees_flagged"] == 0


def test_peer_median_excludes_employee_being_analyzed(proposal_scenario):
    base_employee = proposal_scenario["employee"]
    base_salary = proposal_scenario["salary"]

    peer_salaries = [Decimal("700000"), Decimal("800000"), Decimal("900000")]
    for index, salary_amount in enumerate(peer_salaries, start=2):
        employee = Employee(
            employee_id=f"EMP-TEST-{index:03d}",
            first_name="Peer",
            last_name=str(index),
            email=f"peer{index}@example.com",
            role_id=base_employee.role_id,
            level_id=base_employee.level_id,
            location_id=base_employee.location_id,
            hire_date=date(2023, 1, 1),
            employment_status="ACTIVE",
        )
        db.session.add(employee)
        db.session.flush()

        db.session.add(SalaryRecord(
            salary_id=f"SAL-TEST-{index:03d}",
            employee_id=employee.employee_id,
            band_id=base_salary.band_id,
            base_salary=salary_amount,
            currency_code="INR",
            fte=1.0,
            effective_from=date(2025, 1, 1),
        ))

    db.session.commit()

    report = analyze_compensation()
    subject = next(
        row for row in report["results"]
        if row["employee_id"] == base_employee.employee_id
    )

    assert subject["peer_count"] == 3
    assert subject["peer_group_size"] == 4
    assert subject["peer_median_salary"] == Decimal("800000.00")
    assert any(
        flag["type"] == "PEER_PAY_GAP"
        for flag in subject["potential_issues"]
    )


def test_multiple_active_salary_records_are_excluded(proposal_scenario):
    employee = proposal_scenario["employee"]
    salary = proposal_scenario["salary"]

    db.session.add(SalaryRecord(
        salary_id="SAL-TEST-DUPLICATE",
        employee_id=employee.employee_id,
        band_id=salary.band_id,
        base_salary=Decimal("550000"),
        currency_code="INR",
        fte=1.0,
        effective_from=date(2025, 6, 1),
    ))
    db.session.commit()

    report = analyze_compensation()

    assert report["summary"]["employees_analyzed"] == 0
    assert report["summary"]["employees_excluded"] == 1
    assert report["summary"]["data_quality_issues"][
        "multiple_active_salary_records"
    ] == 1


def test_salary_not_effective_on_historical_date_is_not_analyzed(proposal_scenario):
    report = analyze_compensation(as_of_date="2024-01-01")

    assert report["summary"]["analysis_date"] == "2024-01-01"
    assert report["summary"]["employees_analyzed"] == 0
    assert report["summary"]["data_quality_issues"]["missing_salary"] == 1
