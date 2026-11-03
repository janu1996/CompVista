from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from statistics import median

from sqlalchemy import or_, func

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

    return Decimal(str(value if value is not None else 0))


def money(value):
    """Round money values to 2 decimal places."""

    return to_decimal(value).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )


def normalize_currency(currency_code):
    """Normalize currency codes for safe comparison."""

    return str(currency_code or "").strip().upper()


def analyze_compensation(as_of_date=None):
    """
    Analyze compensation for active employees as of a given date.

    Comparisons are made only within the same:
    - Role
    - Level
    - Location
    - Currency

    Salary is normalized to full-time equivalent (FTE).

    Only effective salary records, compensation bands, and
    performance evidence available on the analysis date
    are considered.

    This function only generates analysis results.
    It does not modify employee salaries.
    """

    # --------------------------------------------------
    # 0. VALIDATE ANALYSIS DATE
    # --------------------------------------------------

    if as_of_date is None:
        as_of_date = date.today()

    if isinstance(as_of_date, str):
        as_of_date = date.fromisoformat(as_of_date)

    if not isinstance(as_of_date, date):
        raise ValueError(
            "as_of_date must be a date object or YYYY-MM-DD string."
        )

    # --------------------------------------------------
    # 1. FETCH ACTIVE EMPLOYEES
    # --------------------------------------------------

    employees = Employee.query.filter(
        Employee.employment_status == "ACTIVE"
    ).all()

    if not employees:
        return {
            "summary": {
                "analysis_date": as_of_date.isoformat(),
                "employees_analyzed": 0,
                "employees_flagged": 0,
                "employees_without_flags": 0,
                "below_band_minimum": 0,
                "low_compa_ratio": 0,
                "peer_pay_gap": 0
            },
            "results": []
        }

    employee_ids = [
        employee.employee_id
        for employee in employees
    ]

    # --------------------------------------------------
    # 2. FETCH EFFECTIVE SALARY RECORDS
    # --------------------------------------------------

    salary_records = SalaryRecord.query.filter(
        SalaryRecord.employee_id.in_(employee_ids),
        SalaryRecord.effective_from <= as_of_date,
        or_(
            SalaryRecord.effective_to.is_(None),
            SalaryRecord.effective_to > as_of_date
        )
    ).order_by(
        SalaryRecord.effective_from.desc(),
        SalaryRecord.salary_id.desc()
    ).all()

    # Keep the latest effective salary record per employee.
    latest_salary = {}

    for record in salary_records:

        if record.employee_id not in latest_salary:
            latest_salary[record.employee_id] = record

    # --------------------------------------------------
    # 3. FETCH EFFECTIVE COMPENSATION BANDS
    # --------------------------------------------------

    bands = CompensationBand.query.filter(
        CompensationBand.effective_from <= as_of_date,
        or_(
            CompensationBand.effective_to.is_(None),
            CompensationBand.effective_to > as_of_date
        )
    ).all()

    band_lookup = {
        band.band_id: band
        for band in bands
    }

    # --------------------------------------------------
    # 4. FETCH PERFORMANCE EVIDENCE
    # --------------------------------------------------

    # Exclude evidence recorded after the analysis date.
    performance_records = PerformanceEvidence.query.filter(
        PerformanceEvidence.employee_id.in_(employee_ids),
        func.date(PerformanceEvidence.recorded_at)
        <= as_of_date.isoformat()
    ).order_by(
        PerformanceEvidence.review_period.desc(),
        PerformanceEvidence.recorded_at.desc()
    ).all()

    latest_performance = {}

    for record in performance_records:

        if record.employee_id not in latest_performance:
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

        # Validate that the salary band belongs to the
        # employee's current role, level, and location.
        if (
            band.role_id != employee.role_id
            or band.level_id != employee.level_id
            or band.location_id != employee.location_id
        ):
            continue

        # Salary and band currencies must match.
        salary_currency = normalize_currency(
            salary.currency_code
        )

        band_currency = normalize_currency(
            band.currency_code
        )

        if (
            not salary_currency
            or salary_currency != band_currency
        ):
            continue

        # Validate FTE.
        actual_salary = to_decimal(salary.base_salary)
        fte = to_decimal(salary.fte)

        if fte <= 0 or fte > 1:
            continue

        if actual_salary <= 0:
            continue

        # Normalize salary to full-time equivalent.
        normalized_salary = money(
            actual_salary / fte
        )

        minimum = money(band.min_salary)
        midpoint = money(band.midpoint_salary)
        maximum = money(band.max_salary)

        # Validate compensation band values.
        if not (
            minimum > 0
            and minimum < midpoint < maximum
        ):
            continue

        # --------------------------------------------------
        # COMPA-RATIO
        # --------------------------------------------------

        compa_ratio = (
            normalized_salary / midpoint
        ) * Decimal("100")

        # --------------------------------------------------
        # BAND POSITION
        # --------------------------------------------------

        band_position = (
            (normalized_salary - minimum)
            / (maximum - minimum)
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
                f"{employee.first_name} {employee.last_name}"
            ),

            "role_id": employee.role_id,
            "level_id": employee.level_id,
            "location_id": employee.location_id,

            "salary_id": salary.salary_id,
            "band_id": band.band_id,

            "currency_code": salary_currency,

            "actual_salary": money(actual_salary),
            "fte": float(fte),
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

        # --------------------------------------------------
        # FLAG 1: BELOW BAND MINIMUM
        # --------------------------------------------------

        if employee_salary < row["band_minimum"]:

            flags.append({
                "type": "BELOW_BAND_MINIMUM",
                "severity": "HIGH",
                "message": (
                    "Employee salary is below the "
                    "applicable compensation band minimum."
                )
            })

        # --------------------------------------------------
        # FLAG 2: LOW COMPA-RATIO
        # --------------------------------------------------

        if row["compa_ratio"] < Decimal("85"):

            flags.append({
                "type": "LOW_COMPA_RATIO",
                "severity": "MEDIUM",
                "message": (
                    "Employee compa-ratio is below 85% "
                    "of the band midpoint."
                )
            })

        # --------------------------------------------------
        # FLAG 3: PEER PAY GAP
        # --------------------------------------------------

        # Require at least 3 other employees.
        if len(peers) >= 4 and peer_median > 0:

            peer_difference = (
                (peer_median - employee_salary)
                / peer_median
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