from app import app
from extensions import db
from models import CompensationBand
from sqlalchemy.exc import IntegrityError

with app.app_context():
    band = CompensationBand.query.first()
    if band is None:
        raise RuntimeError("No compensation band found.")

    original_min = band.min_salary

    try:
        try:
            with db.session.begin_nested():
                band.min_salary = band.midpoint_salary
                db.session.flush()
        except IntegrityError:
            print("Invalid compensation band: PASS - constraint rejected")
        else:
            raise AssertionError("Invalid compensation band was accepted.")
    finally:
        db.session.rollback()

    print("BAND CONSTRAINT TEST FINISHED")
