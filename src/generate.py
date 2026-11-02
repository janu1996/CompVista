
"""
CompVista - Synthetic Compensation Data Generator

Generates:
- 20 Roles
- 5 Career Levels
- 8 Locations
- 5,000 Employees
- 800 Compensation Bands
- Salary History (2023-2026)
- Performance Evidence (2023-2026)
- Employee Tenure
- Promotion History

Uses fixed random seeds for reproducibility.
"""

import os
import sys
import random

from datetime import date, timedelta
from decimal import Decimal

from faker import Faker


# --------------------------------------------------
# BACKEND CONFIGURATION
# --------------------------------------------------

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

BACKEND_PATH = os.path.join(PROJECT_ROOT, "backend")

if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

from app import app
from extensions import db

from models import (
    Employee,
    Role,
    Level,
    Location,
    CompensationBand,
    SalaryRecord,
    PerformanceEvidence,
    Tenure,
    Promotion,
)


# --------------------------------------------------
# RANDOM SEED
# --------------------------------------------------

SEED = 20261022
EMPLOYEE_COUNT = 5000

random.seed(SEED)

fake = Faker("en_IN")
Faker.seed(SEED)


# --------------------------------------------------
# REFERENCE DATA
# --------------------------------------------------

ROLE_DATA = [
    ("Software Engineer", "Engineering", "Technology"),
    ("Frontend Developer", "Engineering", "Technology"),
    ("Backend Developer", "Engineering", "Technology"),
    ("Full Stack Developer", "Engineering", "Technology"),
    ("Data Analyst", "Analytics", "Data"),
    ("Data Scientist", "Analytics", "Data"),
    ("ML Engineer", "AI", "Data"),
    ("DevOps Engineer", "Engineering", "Technology"),
    ("QA Engineer", "Quality", "Technology"),
    ("Product Manager", "Product", "Management"),
    ("UI UX Designer", "Design", "Creative"),
    ("HR Executive", "Human Resources", "Corporate"),
    ("HR Manager", "Human Resources", "Management"),
    ("Finance Analyst", "Finance", "Corporate"),
    ("Business Analyst", "Business", "Corporate"),
    ("Project Manager", "Delivery", "Management"),
    ("Cybersecurity Analyst", "Security", "Technology"),
    ("Cloud Architect", "Engineering", "Technology"),
    ("Technical Writer", "Documentation", "Corporate"),
    ("Customer Success Manager", "Support", "Management"),
]

LEVEL_DATA = [
    ("Intern", 1),
    ("Junior", 2),
    ("Mid-Level", 3),
    ("Senior", 4),
    ("Lead", 5),
]

LOCATION_DATA = [
    ("Visakhapatnam", "India", "IN", "INR", 0.85),
    ("Hyderabad", "India", "IN", "INR", 1.00),
    ("Bengaluru", "India", "IN", "INR", 1.15),
    ("Chennai", "India", "IN", "INR", 0.95),
    ("Pune", "India", "IN", "INR", 1.05),
    ("Mumbai", "India", "IN", "INR", 1.25),
    ("Delhi", "India", "IN", "INR", 1.10),
    ("London", "United Kingdom", "GB", "GBP", 1.40),
]

BASE_SALARIES = {
    "Intern": 300000,
    "Junior": 500000,
    "Mid-Level": 900000,
    "Senior": 1500000,
    "Lead": 2200000,
}

INR_PER_GBP = Decimal("105.00")
CENT = Decimal("0.01")

HISTORY_YEARS = [2023, 2024, 2025, 2026]
DATA_END_DATE = date(2026, 10, 31)


# --------------------------------------------------
# CREATE REFERENCE DATA
# --------------------------------------------------

def create_reference_data():

    if Role.query.count() == 0:

        for name, department, family in ROLE_DATA:

            db.session.add(
                Role(
                    role_name=name,
                    department=department,
                    job_family=family,
                    description=f"{name} position",
                )
            )

    if Level.query.count() == 0:

        for name, rank in LEVEL_DATA:

            db.session.add(
                Level(
                    level_name=name,
                    level_rank=rank,
                    description=f"{name} career level",
                )
            )

    if Location.query.count() == 0:

        for name, country, code, currency, cost_index in LOCATION_DATA:

            db.session.add(
                Location(
                    location_name=name,
                    country=country,
                    country_code=code,
                    currency_code=currency,
                    cost_of_living_index=cost_index,
                )
            )

    db.session.commit()

    print("Reference data created or already available.")


# --------------------------------------------------
# GENERATE EMPLOYEES
# --------------------------------------------------

def generate_employees():

    existing_count = Employee.query.count()

    if existing_count >= EMPLOYEE_COUNT:

        print(
            f"Employee generation skipped. "
            f"{existing_count} employees already exist."
        )
        return

    if existing_count > 0:

        raise RuntimeError(
            f"Only {existing_count} employees exist. "
            "Expected an empty dataset or 5,000 employees."
        )

    roles = Role.query.all()
    levels = Level.query.all()
    locations = Location.query.all()

    if not roles or not levels or not locations:
        raise RuntimeError("Reference data is missing.")

    employees = []

    for number in range(1, EMPLOYEE_COUNT + 1):

        hire_date = fake.date_between(
            start_date=date(2019, 1, 1),
            end_date=DATA_END_DATE,
        )

        employee = Employee(
            employee_id=f"EMP-{number:06d}",
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            email=f"employee{number:06d}@compvista.test",
            role_id=random.choice(roles).role_id,
            level_id=random.choice(levels).level_id,
            location_id=random.choice(locations).location_id,
            hire_date=hire_date,
            employment_status=random.choices(
                [
                    "ACTIVE",
                    "INACTIVE",
                    "ON_LEAVE",
                    "TERMINATED",
                ],
                weights=[85, 5, 5, 5],
            )[0],
        )

        employees.append(employee)

        if len(employees) >= 500:

            db.session.add_all(employees)
            db.session.commit()
            employees.clear()

    if employees:

        db.session.add_all(employees)
        db.session.commit()

    print(f"Generated {EMPLOYEE_COUNT} employees.")


# --------------------------------------------------
# GENERATE COMPENSATION BANDS
# --------------------------------------------------

def generate_compensation_bands():

    existing_count = CompensationBand.query.count()

    if existing_count > 0:

        updated_count = 0

        for band in CompensationBand.query.all():

            if (
                band.effective_from
                and band.effective_from > date(2023, 1, 1)
            ):

                band.effective_from = date(2023, 1, 1)
                updated_count += 1

        if updated_count:
            db.session.commit()

        print(
            f"Compensation band generation skipped. "
            f"{existing_count} bands already exist."
        )

        if updated_count:
            print(
                f"Updated {updated_count} bands to start from 2023."
            )

        return

    roles = Role.query.order_by(Role.role_id).all()
    levels = Level.query.order_by(Level.level_rank).all()
    locations = Location.query.order_by(Location.location_id).all()

    bands = []

    for role_index, role in enumerate(roles):

        role_multiplier = Decimal(
            str(0.90 + (role_index % 5) * 0.05)
        )

        for level in levels:

            base_salary = Decimal(
                str(BASE_SALARIES[level.level_name])
            )

            for location in locations:

                cost_multiplier = Decimal(
                    str(location.cost_of_living_index)
                )

                midpoint = (
                    base_salary
                    * role_multiplier
                    * cost_multiplier
                )

                if location.currency_code == "GBP":
                    midpoint /= INR_PER_GBP

                midpoint = midpoint.quantize(CENT)

                minimum = (
                    midpoint * Decimal("0.80")
                ).quantize(CENT)

                maximum = (
                    midpoint * Decimal("1.20")
                ).quantize(CENT)

                bands.append(
                    CompensationBand(
                        band_id=(
                            f"BAND-{role.role_id}-"
                            f"{level.level_id}-"
                            f"{location.location_id}"
                        ),
                        role_id=role.role_id,
                        level_id=level.level_id,
                        location_id=location.location_id,
                        min_salary=minimum,
                        midpoint_salary=midpoint,
                        max_salary=maximum,
                        currency_code=location.currency_code,
                        effective_from=date(2023, 1, 1),
                        effective_to=None,
                    )
                )

    db.session.add_all(bands)
    db.session.commit()

    print(f"Generated {len(bands)} compensation bands.")


# --------------------------------------------------
# GENERATE SALARY HISTORY
# --------------------------------------------------

def generate_salary_history():

    employees = Employee.query.order_by(
        Employee.employee_id
    ).all()

    bands = CompensationBand.query.all()

    if not employees or not bands:
        raise RuntimeError("Employees or bands are missing.")

    existing_records = {
        record.salary_id
        for record in SalaryRecord.query.all()
    }

    band_lookup = {
        (
            band.role_id,
            band.level_id,
            band.location_id,
        ): band
        for band in bands
    }

    records_batch = []

    generated = 0
    skipped = 0

    rng = random.Random(SEED + 10)

    for employee in employees:

        band = band_lookup.get(
            (
                employee.role_id,
                employee.level_id,
                employee.location_id,
            )
        )

        if band is None:
            raise RuntimeError(
                f"Missing band for {employee.employee_id}"
            )

        fte = rng.choices(
            [1.0, 0.75, 0.5],
            weights=[90, 6, 4],
        )[0]

        fte_decimal = Decimal(str(fte))

        annual_salary = (
            Decimal(str(band.midpoint_salary))
            * Decimal(str(rng.uniform(0.82, 0.90)))
        ).quantize(CENT)

        effective_dates = []

        for year in HISTORY_YEARS:

            year_start = date(year, 1, 1)
            year_end = date(year, 12, 31)

            if employee.hire_date > year_end:
                continue

            start = max(year_start, employee.hire_date)

            if start <= DATA_END_DATE:
                effective_dates.append((year, start))

        for index, (year, start_date) in enumerate(effective_dates):

            salary_id = f"SAL-{employee.employee_id}-{year}"

            if salary_id in existing_records:
                skipped += 1
                continue

            if index > 0:

                annual_salary = (
                    annual_salary
                    * Decimal(str(rng.uniform(1.03, 1.08)))
                ).quantize(CENT)

            minimum = (
                Decimal(str(band.min_salary))
                * Decimal("1.01")
            )

            maximum = (
                Decimal(str(band.max_salary))
                * Decimal("0.96")
            )

            annual_salary = max(annual_salary, minimum)
            annual_salary = min(annual_salary, maximum)

            actual_salary = (
                annual_salary * fte_decimal
            ).quantize(CENT)

            end_date = None

            if index < len(effective_dates) - 1:
                end_date = effective_dates[index + 1][1]

            records_batch.append(
                SalaryRecord(
                    salary_id=salary_id,
                    employee_id=employee.employee_id,
                    band_id=band.band_id,
                    base_salary=actual_salary,
                    currency_code=band.currency_code,
                    fte=fte,
                    effective_from=start_date,
                    effective_to=end_date,
                    change_reason=(
                        "Initial salary record"
                        if index == 0
                        else "Annual merit increase"
                    ),
                )
            )

            existing_records.add(salary_id)
            generated += 1

            if len(records_batch) >= 500:

                try:
                    db.session.add_all(records_batch)
                    db.session.commit()
                    records_batch.clear()

                except Exception:
                    db.session.rollback()
                    raise

    if records_batch:

        try:
            db.session.add_all(records_batch)
            db.session.commit()

        except Exception:
            db.session.rollback()
            raise

    print("\nSalary History Generation")
    print("---------------------------")
    print("New records generated:", generated)
    print("Existing records skipped:", skipped)
    print("Total salary records:", SalaryRecord.query.count())


# --------------------------------------------------
# GENERATE PERFORMANCE EVIDENCE
# --------------------------------------------------

def generate_performance_evidence():

    employees = Employee.query.order_by(
        Employee.employee_id
    ).all()

    existing_ids = {
        record.evidence_id
        for record in PerformanceEvidence.query.all()
    }

    rng = random.Random(SEED + 1)

    evidence_types = [
        "ANNUAL_REVIEW",
        "GOAL_ACHIEVEMENT",
        "SKILL_ASSESSMENT",
    ]

    rating_weights = [5, 10, 25, 40, 20]

    descriptions = {
        1: "Performance improvement required. "
           "Several assigned objectives were not achieved.",

        2: "Developing performance. "
           "Some objectives were achieved with additional support.",

        3: "Meets expectations. "
           "Expected responsibilities and goals were completed.",

        4: "Strong performance. "
           "Frequently exceeded assigned goals and expectations.",

        5: "Outstanding performance. "
           "Consistently delivered exceptional results.",
    }

    records_batch = []

    generated = 0
    skipped = 0

    for employee in employees:

        for year in HISTORY_YEARS:

            if employee.hire_date > date(year, 12, 31):
                continue

            evidence_id = (
                f"PERF-{employee.employee_id}-{year}"
            )

            if evidence_id in existing_ids:
                skipped += 1
                continue

            rating = rng.choices(
                [1, 2, 3, 4, 5],
                weights=rating_weights,
            )[0]

            records_batch.append(
                PerformanceEvidence(
                    evidence_id=evidence_id,
                    employee_id=employee.employee_id,
                    review_period=str(year),
                    performance_rating=float(rating),
                    rating_scale="1-5",
                    evidence_type=rng.choice(evidence_types),
                    description=descriptions[rating],
                    recorded_by="CompVista HR Review Team",
                )
            )

            existing_ids.add(evidence_id)
            generated += 1

            if len(records_batch) >= 500:

                try:
                    db.session.add_all(records_batch)
                    db.session.commit()
                    records_batch.clear()

                except Exception:
                    db.session.rollback()
                    raise

    if records_batch:

        try:
            db.session.add_all(records_batch)
            db.session.commit()

        except Exception:
            db.session.rollback()
            raise

    print("\nPerformance Evidence Generation")
    print("--------------------------------")
    print("New records generated:", generated)
    print("Existing records skipped:", skipped)
    print(
        "Total performance records:",
        PerformanceEvidence.query.count(),
    )


# --------------------------------------------------
# GENERATE TENURE
# --------------------------------------------------

def generate_tenure():

    employees = Employee.query.order_by(
        Employee.employee_id
    ).all()

    existing_ids = {
        record.tenure_id
        for record in Tenure.query.all()
    }

    # Use the latest salary record's FTE so tenure and
    # salary records use a consistent FTE value.
    latest_salary_fte = {}

    salary_records = SalaryRecord.query.order_by(
        SalaryRecord.effective_from.desc()
    ).all()

    for salary in salary_records:

        if salary.employee_id not in latest_salary_fte:
            latest_salary_fte[salary.employee_id] = salary.fte

    rng = random.Random(SEED + 2)

    records_batch = []

    generated = 0
    skipped = 0

    for employee in employees:

        tenure_id = f"TEN-{employee.employee_id}"

        if tenure_id in existing_ids:
            skipped += 1
            continue

        fte = latest_salary_fte.get(
            employee.employee_id,
            1.0,
        )

        tenure_type = (
            "FULL_TIME"
            if fte == 1.0
            else "PART_TIME"
        )

        end_date = None

        if employee.employment_status in [
            "INACTIVE",
            "TERMINATED",
        ]:

            earliest_end = employee.hire_date + timedelta(days=1)

            if earliest_end <= DATA_END_DATE:

                end_date = rng.choice(
                    [
                        earliest_end
                        + timedelta(
                            days=rng.randint(
                                0,
                                max(
                                    0,
                                    (DATA_END_DATE - earliest_end).days
                                ),
                            )
                        )
                    ]
                )

        records_batch.append(
            Tenure(
                tenure_id=tenure_id,
                employee_id=employee.employee_id,
                start_date=employee.hire_date,
                end_date=end_date,
                tenure_type=tenure_type,
                fte=fte,
            )
        )

        existing_ids.add(tenure_id)
        generated += 1

        if len(records_batch) >= 500:

            try:
                db.session.add_all(records_batch)
                db.session.commit()
                records_batch.clear()

            except Exception:
                db.session.rollback()
                raise

    if records_batch:

        try:
            db.session.add_all(records_batch)
            db.session.commit()

        except Exception:
            db.session.rollback()
            raise

    print("\nTenure Generation")
    print("-----------------")
    print("New records generated:", generated)
    print("Existing records skipped:", skipped)
    print("Total tenure records:", Tenure.query.count())


# --------------------------------------------------
# GENERATE PROMOTIONS
# --------------------------------------------------

def generate_promotions():

    employees = Employee.query.order_by(
        Employee.employee_id
    ).all()

    levels = Level.query.order_by(
        Level.level_rank
    ).all()

    level_lookup = {
        level.level_id: level
        for level in levels
    }

    previous_level_lookup = {
        level.level_rank: level
        for level in levels
    }

    existing_ids = {
        promotion.promotion_id
        for promotion in Promotion.query.all()
    }

    rng = random.Random(SEED + 3)

    records_batch = []

    generated = 0
    skipped = 0

    for employee in employees:

        promotion_id = f"PROM-{employee.employee_id}"

        if promotion_id in existing_ids:
            skipped += 1
            continue

        current_level = level_lookup.get(employee.level_id)

        if current_level is None:
            raise RuntimeError(
                f"Missing current level for {employee.employee_id}"
            )

        # Level 1 has no lower career level to promote from.
        if current_level.level_rank <= 1:
            continue

        previous_level = previous_level_lookup.get(
            current_level.level_rank - 1
        )

        if previous_level is None:
            continue

        # Employee should have at least one year of service
        # before the promotion date.
        earliest_promotion = max(
            employee.hire_date + timedelta(days=365),
            date(2023, 1, 1),
        )

        latest_promotion = date(2025, 12, 31)

        if earliest_promotion > latest_promotion:
            continue

        promotion_date = earliest_promotion + timedelta(
            days=rng.randint(
                0,
                (latest_promotion - earliest_promotion).days,
            )
        )

        records_batch.append(
            Promotion(
                promotion_id=promotion_id,
                employee_id=employee.employee_id,

                # Role remains the same in this example.
                previous_role_id=employee.role_id,
                new_role_id=employee.role_id,

                # Career level increases by one.
                previous_level_id=previous_level.level_id,
                new_level_id=current_level.level_id,

                promotion_date=promotion_date,

                reason=(
                    f"Career progression from "
                    f"{previous_level.level_name} to "
                    f"{current_level.level_name} "
                    "based on performance and experience."
                ),

                approved_by="CompVista HR Manager",
            )
        )

        existing_ids.add(promotion_id)
        generated += 1

        if len(records_batch) >= 500:

            try:
                db.session.add_all(records_batch)
                db.session.commit()
                records_batch.clear()

            except Exception:
                db.session.rollback()
                raise

    if records_batch:

        try:
            db.session.add_all(records_batch)
            db.session.commit()

        except Exception:
            db.session.rollback()
            raise

    print("\nPromotion Generation")
    print("--------------------")
    print("New records generated:", generated)
    print("Existing records skipped:", skipped)
    print("Total promotion records:", Promotion.query.count())


# --------------------------------------------------
# MAIN FUNCTION
# --------------------------------------------------

def main():

    print("\nStarting CompVista data generation...\n")

    with app.app_context():

        try:

            create_reference_data()

            generate_employees()

            generate_compensation_bands()

            generate_salary_history()

            generate_performance_evidence()

            generate_tenure()

            generate_promotions()

            print("\nCOMPVISTA DATABASE SUMMARY")
            print("============================")

            print("Employees:", Employee.query.count())
            print("Roles:", Role.query.count())
            print("Levels:", Level.query.count())
            print("Locations:", Location.query.count())

            print(
                "Compensation Bands:",
                CompensationBand.query.count(),
            )

            print(
                "Salary Records:",
                SalaryRecord.query.count(),
            )

            print(
                "Performance Evidence:",
                PerformanceEvidence.query.count(),
            )

            print(
                "Tenure Records:",
                Tenure.query.count(),
            )

            print(
                "Promotion Records:",
                Promotion.query.count(),
            )

            print(
                "\nCompVista data generation completed successfully!"
            )

        except Exception:

            db.session.rollback()
            raise


# --------------------------------------------------
# EXECUTION
# --------------------------------------------------

if __name__ == "__main__":
    main()
