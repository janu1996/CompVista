
from extensions import db
from sqlalchemy import Numeric


class SalaryRecord(db.Model):
    __tablename__ = "salary_records"

    # Database validations
    __table_args__ = (
        db.CheckConstraint(
            "fte > 0 AND fte <= 1",
            name="check_valid_salary_fte"
        ),
        db.CheckConstraint(
            "effective_to IS NULL OR effective_to > effective_from",
            name="check_valid_salary_dates"
        ),
        db.CheckConstraint(
            "base_salary > 0",
            name="check_positive_base_salary"
        ),
    )

    # Primary Key
    salary_id = db.Column(
        db.String(30),
        primary_key=True
    )

    # Foreign Keys
    employee_id = db.Column(
        db.String(20),
        db.ForeignKey("employees.employee_id"),
        nullable=False
    )

    band_id = db.Column(
        db.String(100),
        db.ForeignKey("compensation_bands.band_id"),
        nullable=False
    )

    # Salary Details
    base_salary = db.Column(
        Numeric(14, 2),
        nullable=False
    )

    currency_code = db.Column(
        db.String(5),
        nullable=False
    )

    fte = db.Column(
        db.Float,
        nullable=False,
        default=1.0
    )

    # Effective Dates
    effective_from = db.Column(
        db.Date,
        nullable=False
    )

    effective_to = db.Column(
        db.Date,
        nullable=True
    )

    change_reason = db.Column(
        db.String(200)
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    def __repr__(self):
        return f"<SalaryRecord {self.salary_id}>"
