
from datetime import date

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
        "peer_pay_gap"
    ]

    for field in expected_fields:
        assert field in summary


def test_analysis_with_as_of_date():
    report = analyze_compensation(
        as_of_date=date(2026, 1, 1)
    )

    assert isinstance(report, dict)
    assert "summary" in report
    assert "results" in report


def test_empty_database_returns_zero_employees():
    report = analyze_compensation()

    summary = report["summary"]

    assert summary["employees_analyzed"] == 0
    assert summary["employees_flagged"] == 0
