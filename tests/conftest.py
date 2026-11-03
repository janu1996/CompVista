
import os
import sys
import pytest
from pathlib import Path
from datetime import date

# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_PATH = PROJECT_ROOT / "backend"

sys.path.insert(0, str(BACKEND_PATH))


# --------------------------------------------------
# TEST APPLICATION
# --------------------------------------------------

@pytest.fixture(scope="session")
def app(tmp_path_factory):

    test_db_dir = tmp_path_factory.mktemp("compvista_test")
    test_db_path = test_db_dir / "test_compvista.db"

    from app import app as flask_app
    from extensions import db

    flask_app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{test_db_path.as_posix()}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    with flask_app.app_context():
        db.create_all()

    yield flask_app

    with flask_app.app_context():
        db.session.remove()
        db.drop_all()


# --------------------------------------------------
# CLEAN DATABASE BEFORE AND AFTER EACH TEST
# --------------------------------------------------

@pytest.fixture(autouse=True)
def clean_database(app):

    from extensions import db

    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.create_all()

        yield

        db.session.remove()
        db.drop_all()


# --------------------------------------------------
# FLASK TEST CLIENT
# --------------------------------------------------

@pytest.fixture
def client(app):
    return app.test_client()


# --------------------------------------------------
# SYNTHETIC PROPOSAL TEST DATA
# --------------------------------------------------

@pytest.fixture
def proposal_scenario():

    from extensions import db

    from models import (
        Role,
        Level,
        Location,
        Employee,
        CompensationBand,
        SalaryRecord
    )

    # 1. Create role, level and location

    role = Role(
        role_name="Test Software Engineer",
        department="Engineering",
        job_family="Software Development"
    )

    level = Level(
        level_name="Test L2",
        level_rank=2
    )

    location = Location(
        location_name="Test Hyderabad",
        country="India",
        country_code="IN",
        currency_code="INR",
        cost_of_living_index=1.0
    )

    db.session.add_all([role, level, location])
    db.session.flush()

    # 2. Create employee

    employee = Employee(
        employee_id="EMP-TEST-001",
        first_name="Test",
        last_name="Employee",
        email="test.employee@example.com",
        role_id=role.role_id,
        level_id=level.level_id,
        location_id=location.location_id,
        hire_date=date(2023, 1, 1),
        employment_status="ACTIVE"
    )

    # 3. Create compensation band

    band = CompensationBand(
        band_id="BAND-TEST-001",
        role_id=role.role_id,
        level_id=level.level_id,
        location_id=location.location_id,
        min_salary=400000,
        midpoint_salary=800000,
        max_salary=1200000,
        currency_code="INR",
        effective_from=date(2025, 1, 1)
    )

    db.session.add_all([employee, band])
    db.session.flush()

    # 4. Create salary record

    salary = SalaryRecord(
        salary_id="SAL-TEST-001",
        employee_id=employee.employee_id,
        band_id=band.band_id,
        base_salary=500000,
        currency_code="INR",
        fte=1.0,
        effective_from=date(2025, 1, 1)
    )

    db.session.add(salary)
    db.session.commit()

    return {
        "employee": employee,
        "band": band,
        "salary": salary
    }
