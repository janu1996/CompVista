
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from statistics import median

from sqlalchemy import or_, func

from models import (
    Employee,
    SalaryRecord,
    CompensationBand,
    PerformanceEvidence,
)
from services.fx_service import convert_to_inr


def to_decimal(value):
    """Convert a value safely into Decimal."""
    return Decimal(str(value if value is not None else 0))


def money(value):
    """Round money values to two decimal places."""
    return to_decimal(value).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


def normalize_currency(currency_code):
    """Normalize currency codes for safe comparison."""
    return str(currency_code or "").strip().upper()


def _empty_summary(as_of_date):
    return {
        "analysis_date": as_of_date.isoformat(),
        "reporting_currency": "INR",
        "employees_analyzed": 0,
        "employees_flagged": 0,
        "employees_without_flags": 0,
        "below_band_minimum": 0,
        "low_compa_ratio": 0,
        "peer_pay_gap": 0,
        "employees_excluded": 0,
        "data_quality_issues": {
            "missing_salary": 0,
            "multiple_active_salary_records": 0,
            "missing_or_inactive_band": 0,
            "employee_band_mismatch": 0,
            "currency_mismatch": 0,
            "invalid_salary_or_fte": 0,
            "invalid_band": 0,
            "missing_fx_rate": 0,
        },
    }


def analyze_compensation(as_of_date=None):
    """Analyze active employees' compensation as of a given date.

    Original currency amounts and existing local-currency peer comparisons
    are preserved. Additional INR-normalized values support consolidated
    reporting.

    Peer comparisons remain restricted to the same role, level, location,
    and currency. The subject employee is excluded from their own median.

    This function is read-only: it does not modify employee or salary data.
    """
    if as_of_date is None:
        as_of_date = date.today()
    elif isinstance(as_of_date, str):
        try:
            as_of_date = date.fromisoformat(as_of_date)
        except ValueError as exc:
            raise ValueError(
                "as_of_date must use YYYY-MM-DD format."
            ) from exc
    elif isinstance(as_of_date, datetime):
        as_of_date = as_of_date.date()

    if not isinstance(as_of_date, date):
        raise ValueError(
            "as_of_date must be a date object or YYYY-MM-DD string."
        )

    summary = _empty_summary(as_of_date)
    quality = summary["data_quality_issues"]

    employees = Employee.query.filter_by(
        employment_status="ACTIVE"
    ).all()

    if not employees:
        return {"summary": summary, "results": []}

    employee_ids = [employee.employee_id for employee in employees]

    salary_records = SalaryRecord.query.filter(
        SalaryRecord.employee_id.in_(employee_ids),
        SalaryRecord.effective_from <= as_of_date,
        or_(
            SalaryRecord.effective_to.is_(None),
            SalaryRecord.effective_to > as_of_date,
        ),
    ).order_by(
        SalaryRecord.effective_from.desc(),
        SalaryRecord.salary_id.desc(),
    ).all()

    salaries_by_employee = {}
    for record in salary_records:
        salaries_by_employee.setdefault(
            record.employee_id, []
        ).append(record)

    bands = CompensationBand.query.filter(
        CompensationBand.effective_from <= as_of_date,
        or_(
            CompensationBand.effective_to.is_(None),
            CompensationBand.effective_to > as_of_date,
        ),
    ).all()

    band_lookup = {
        band.band_id: band for band in bands
    }

    performance_records = PerformanceEvidence.query.filter(
        PerformanceEvidence.employee_id.in_(employee_ids),
        func.date(PerformanceEvidence.recorded_at)
        <= as_of_date.isoformat(),
    ).order_by(
        PerformanceEvidence.review_period.desc(),
        PerformanceEvidence.recorded_at.desc(),
    ).all()

    latest_performance = {}
    for record in performance_records:
        latest_performance.setdefault(
            record.employee_id, record
        )

    analysis_rows = []

    for employee in employees:
        employee_salaries = salaries_by_employee.get(
            employee.employee_id, []
        )

        if not employee_salaries:
            quality["missing_salary"] += 1
            continue

        if len(employee_salaries) != 1:
            quality["multiple_active_salary_records"] += 1
            continue

        salary = employee_salaries[0]
        band = band_lookup.get(salary.band_id)

        if band is None:
            quality["missing_or_inactive_band"] += 1
            continue

        if (
            band.role_id != employee.role_id
            or band.level_id != employee.level_id
            or band.location_id != employee.location_id
        ):
            quality["employee_band_mismatch"] += 1
            continue

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
            quality["currency_mismatch"] += 1
            continue

        try:
            actual_salary = to_decimal(salary.base_salary)
            fte = to_decimal(salary.fte)

            if (
                not actual_salary.is_finite()
                or not fte.is_finite()
                or actual_salary <= 0
                or fte <= 0
                or fte > 1
            ):
                quality["invalid_salary_or_fte"] += 1
                continue

            normalized_salary = money(actual_salary / fte)

            minimum = money(band.min_salary)
            midpoint = money(band.midpoint_salary)
            maximum = money(band.max_salary)

        except (
            InvalidOperation,
            TypeError,
            ValueError,
            ZeroDivisionError,
        ):
            quality["invalid_salary_or_fte"] += 1
            continue

        if not (
            minimum.is_finite()
            and midpoint.is_finite()
            and maximum.is_finite()
            and Decimal("0") < minimum < midpoint < maximum
        ):
            quality["invalid_band"] += 1
            continue

        # Convert all compensation values using the same analysis date.
        try:
            salary_inr = convert_to_inr(
                normalized_salary,
                salary_currency,
                as_of_date,
            )

            minimum_inr = convert_to_inr(
                minimum,
                band_currency,
                as_of_date,
            )

            midpoint_inr = convert_to_inr(
                midpoint,
                band_currency,
                as_of_date,
            )

            maximum_inr = convert_to_inr(
                maximum,
                band_currency,
                as_of_date,
            )

        except ValueError:
            quality["missing_fx_rate"] += 1
            continue

        fx_rate = salary_inr["exchange_rate"]

        compa_ratio = (
            normalized_salary / midpoint
        ) * Decimal("100")

        band_position = (
            (normalized_salary - minimum)
            / (maximum - minimum)
        ) * Decimal("100")

        performance = latest_performance.get(
            employee.employee_id
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

            # Original currency values
            "currency_code": salary_currency,
            "actual_salary": money(actual_salary),
            "fte": float(fte),
            "normalized_salary": normalized_salary,
            "band_minimum": minimum,
            "band_midpoint": midpoint,
            "band_maximum": maximum,

            # INR-normalized values
            "reporting_currency": "INR",
            "normalized_salary_inr": (
                salary_inr["converted_amount"]
            ),
            "band_minimum_inr": (
                minimum_inr["converted_amount"]
            ),
            "band_midpoint_inr": (
                midpoint_inr["converted_amount"]
            ),
            "band_maximum_inr": (
                maximum_inr["converted_amount"]
            ),

            # FX metadata
            "fx_rate": fx_rate,
            "fx_source": "SYNTHETIC_DATASET",
            "fx_effective_date": as_of_date.isoformat(),

            # Existing analysis metrics
            "compa_ratio": money(compa_ratio),
            "band_position": money(band_position),
            "performance_rating": (
                performance.performance_rating
                if performance else None
            ),
        })

    # Preserve the existing comparable-group definition.
    peer_groups = {}

    for row in analysis_rows:
        group_key = (
            row["role_id"],
            row["level_id"],
            row["location_id"],
            row["currency_code"],
        )
        peer_groups.setdefault(group_key, []).append(row)

    results = []

    for row in analysis_rows:
        group_key = (
            row["role_id"],
            row["level_id"],
            row["location_id"],
            row["currency_code"],
        )

        group = peer_groups[group_key]

        other_peers = [
            peer for peer in group
            if peer["employee_id"] != row["employee_id"]
        ]

        peer_median = (
            money(
                median([
                    peer["normalized_salary"]
                    for peer in other_peers
                ])
            )
            if other_peers else None
        )

        peer_median_inr = (
            money(
                median([
                    peer["normalized_salary_inr"]
                    for peer in other_peers
                ])
            )
            if other_peers else None
        )

        flags = []
        employee_salary = row["normalized_salary"]

        if employee_salary < row["band_minimum"]:
            flags.append({
                "type": "BELOW_BAND_MINIMUM",
                "severity": "HIGH",
                "message": (
                    "Employee salary is below the applicable "
                    "compensation band minimum."
                ),
            })

        if row["compa_ratio"] < Decimal("85"):
            flags.append({
                "type": "LOW_COMPA_RATIO",
                "severity": "MEDIUM",
                "message": (
                    "Employee compa-ratio is below 85% "
                    "of the band midpoint."
                ),
            })

        # Require at least three comparable employees,
        # excluding the subject employee.
        if (
            len(other_peers) >= 3
            and peer_median is not None
            and peer_median > 0
        ):
            peer_difference = (
                (peer_median - employee_salary)
                / peer_median
            ) * Decimal("100")

            if peer_difference >= Decimal("10"):
                flags.append({
                    "type": "PEER_PAY_GAP",
                    "severity": "MEDIUM",
                    "message": (
                        "Employee salary is at least 10% below the "
                        "comparable group median."
                    ),
                })

        result = dict(row)

        result.update({
            "peer_group_size": len(group),
            "peer_count": len(other_peers),
            "peer_median_salary": peer_median,
            "peer_median_salary_inr": peer_median_inr,
            "potential_issues": flags,
            "requires_hr_review": bool(flags),
        })

        results.append(result)

    flagged = [
        row for row in results
        if row["requires_hr_review"]
    ]

    summary.update({
        "employees_analyzed": len(results),
        "employees_flagged": len(flagged),
        "employees_without_flags": (
            len(results) - len(flagged)
        ),
        "below_band_minimum": sum(
            any(
                flag["type"] == "BELOW_BAND_MINIMUM"
                for flag in row["potential_issues"]
            )
            for row in results
        ),
        "low_compa_ratio": sum(
            any(
                flag["type"] == "LOW_COMPA_RATIO"
                for flag in row["potential_issues"]
            )
            for row in results
        ),
        "peer_pay_gap": sum(
            any(
                flag["type"] == "PEER_PAY_GAP"
                for flag in row["potential_issues"]
            )
            for row in results
        ),
        "employees_excluded": sum(quality.values()),
    })

    return {
        "summary": summary,
        "results": results,
    }
