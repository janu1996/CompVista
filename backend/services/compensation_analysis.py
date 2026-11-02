
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from statistics import median

from models import (
    Employee,
    SalaryRecord,
    CompensationBand,
    PerformanceEvidence
)


# --------------------------------------------------
# COMPVISTA COMPENSATION ANALYSIS ENGINE
# --------------------------------------------------

def to_decimal(value):
    """Convert a value safely into Decimal."""

    return Decimal(str(value or 0))


def money(value):
    """Round money values to 2 decimal places."""

    return to_decimal(value).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )


def analyze_compensation(as_of_date=None):
    """
    Analyze current compensation for active employees.

    Comparisons are made only within the same:
    - Role
    - Level
    - Location
    - Currency

    Salary is normalized to full-time equivalent (FTE)
    before comparison.

    This function creates analysis results only.
    It does not automatically change employee salaries.
    """

    if as_of_date is None:
        as_of_date = date.today()

    # --------------------------------------------------
    # 1. FETCH ACTIVE EMPLOYEES
    # --------------------------------------------------

    employees = Employee.query.filter(
        Employee.employment_status == "ACTIVE"
    ).all()

    # --------------------------------------------------
    # 2. FETCH EFFECTIVE SALARY RECORDS
    # --------------------------------------------------

    salary_records = SalaryRecord.query.filter(
        SalaryRecord.effective_from <= as_of_date,
        db_or := (
            (SalaryRecord.effective_to.is_(None)) |
            (SalaryRecord.effective_to > as_of_date)
        )
    ).order_by(
        SalaryRecord.effective_from.desc()
    ).all()

    # Keep the latest effective salary record per employee.
    latest_salary = {}

    for record in salary_records:

        if record.employee_id not in latest_salary:

            latest_salary[record.employee_id] = record

    # --------------------------------------------------
    # 3. FETCH COMPENSATION BANDS
    # --------------------------------------------------

    bands = CompensationBand.query.filter(
        CompensationBand.effective_from <= as_of_date,
        (
            CompensationBand.effective_to.is_(None) |
            (CompensationBand.effective_to > as_of_date)
        )
    ).all()

    band_lookup = {
        band.band_id: band
        for band in bands
    }

    # --------------------------------------------------
    # 4. FETCH PERFORMANCE EVIDENCE
    # --------------------------------------------------

    performance_records = PerformanceEvidence.query.all()

    latest_performance = {}

    for record in performance_records:

        current = latest_performance.get(record.employee_id)

        if (
            current is None
            or record.review_period > current.review_period
        ):
            latest_performance[record.employee_id] = record

    # --------------------------------------------------
    # 5. BUILD EMPLOYEE COMPENSATION DATA
    # --------------------------------------------------

    analysis_rows = []

    for employee in employees:

        salary = latest_salary.get(employee.employee_id)

        if salary is None:
            continue

        band = band_lookup.get(salary.band_id)

        if band is None:
            continue

        if salary.fte <= 0:
            continue

        # Normalize salary to full-time equivalent.
        actual_salary = to_decimal(salary.base_salary)

        fte = to_decimal(salary.fte)

        normalized_salary = money(
            actual_salary / fte
        )

        minimum = money(band.min_salary)
        midpoint = money(band.midpoint_salary)
        maximum = money(band.max_salary)

        if midpoint <= 0 or maximum <= minimum:
            continue

        # Compa-ratio.
        compa_ratio = (
            normalized_salary / midpoint
        ) * Decimal("100")

        # Position within salary band.
        band_position = (
            (normalized_salary - minimum) /
            (maximum - minimum)
        ) * Decimal("100")

        performance = latest_performance.get(
            employee.employee_id
        )

        performance_rating = (
            performance.performance_rating
            if performance else None
        )

        analysis_rows.append({
            "employee_id": employee.employee_id,
            "employee_name": (
                employee.first_name + " " + employee.last_name
            ),
            "role_id": employee.role_id,
            "level_id": employee.level_id,
            "location_id": employee.location_id,

            "salary_id": salary.salary_id,
            "band_id": band.band_id,

            "currency_code": salary.currency_code,
            "actual_salary": money(actual_salary),
            "fte": float(salary.fte),
            "normalized_salary": normalized_salary,

            "band_minimum": minimum,
            "band_midpoint": midpoint,
            "band_maximum": maximum,

            "compa_ratio": money(compa_ratio),
            "band_position": money(band_position),

            "performance_rating": performance_rating
        })

    # --------------------------------------------------
    # 6. CREATE COMPARABLE EMPLOYEE GROUPS
    # --------------------------------------------------

    peer_groups = {}

    for row in analysis_rows:

        group_key = (
            row["role_id"],
            row["level_id"],
            row["location_id"],
            row["currency_code"]
        )

        peer_groups.setdefault(
            group_key,
            []
        ).append(row)

    # --------------------------------------------------
    # 7. ANALYZE POTENTIAL DISPARITIES
    # --------------------------------------------------

    results = []

    for row in analysis_rows:

        group_key = (
            row["role_id"],
            row["level_id"],
            row["location_id"],
            row["currency_code"]
        )

        peers = peer_groups[group_key]

        peer_salaries = [
            peer["normalized_salary"]
            for peer in peers
        ]

        peer_median = money(
            median(peer_salaries)
        )

        employee_salary = row["normalized_salary"]

        flags = []

        # Flag 1: Salary below the band minimum.
        if employee_salary < row["band_minimum"]:

            flags.append({
                "type": "BELOW_BAND_MINIMUM",
                "severity": "HIGH",
                "message": (
                    "Employee salary is below the "
                    "applicable compensation band minimum."
                )
            })

        # Flag 2: Low compa-ratio.
        if row["compa_ratio"] < Decimal("85"):

            flags.append({
                "type": "LOW_COMPA_RATIO",
                "severity": "MEDIUM",
                "message": (
                    "Employee compa-ratio is below 85% "
                    "of the band midpoint."
                )
            })

        # Flag 3: Lower salary compared with peers.
        # Require at least 3 other employees.
        if len(peers) >= 4 and peer_median > 0:

            peer_difference = (
                (peer_median - employee_salary) /
                peer_median
            ) * Decimal("100")

            if peer_difference >= Decimal("10"):

                flags.append({
                    "type": "PEER_PAY_GAP",
                    "severity": "MEDIUM",
                    "message": (
                        "Employee salary is at least 10% "
                        "below the comparable group median."
                    )
                })

        # --------------------------------------------------
        # 8. ADD FINAL ANALYSIS RESULT
        # --------------------------------------------------

        result = dict(row)

        result.update({
            "peer_group_size": len(peers),
            "peer_median_salary": peer_median,
            "potential_issues": flags,
            "requires_hr_review": len(flags) > 0
        })

        results.append(result)

    # --------------------------------------------------
    # 9. GENERATE SUMMARY
    # --------------------------------------------------

    flagged_employees = [
        row for row in results
        if row["requires_hr_review"]
    ]

    summary = {
        "analysis_date": as_of_date.isoformat(),
        "employees_analyzed": len(results),
        "employees_flagged": len(flagged_employees),
        "employees_without_flags": (
            len(results) - len(flagged_employees)
        ),
        "below_band_minimum": sum(
            1 for row in results
            if any(
                flag["type"] == "BELOW_BAND_MINIMUM"
                for flag in row["potential_issues"]
            )
        ),
        "low_compa_ratio": sum(
            1 for row in results
            if any(
                flag["type"] == "LOW_COMPA_RATIO"
                for flag in row["potential_issues"]
            )
        ),
        "peer_pay_gap": sum(
            1 for row in results
            if any(
                flag["type"] == "PEER_PAY_GAP"
                for flag in row["potential_issues"]
            )
        )
    }

    return {
        "summary": summary,
        "results": results
    }


# --------------------------------------------------
# IMPORT REQUIRED SQLALCHEMY EXPRESSION
# --------------------------------------------------

from sqlalchemy import or_ as db_or
