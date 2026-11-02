
from extensions import db


class SalaryRecord(db.Model):
    __tablename__ = "salary_records"

    salary_id = db.Column(db.String(30), primary_key=True)

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

    base_salary = db.Column(db.Float, nullable=False)

    currency_code = db.Column(db.String(5), nullable=False)

    fte = db.Column(db.Float, nullable=False, default=1.0)

    effective_from = db.Column(db.Date, nullable=False)
    effective_to = db.Column(db.Date, nullable=True)

    change_reason = db.Column(db.String(200))

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    def __repr__(self):
        return f"<SalaryRecord {self.salary_id}>"
