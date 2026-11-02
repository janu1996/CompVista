
from extensions import db


class Tenure(db.Model):
    __tablename__ = "tenures"

    __table_args__ = (
        db.CheckConstraint(
            "fte > 0 AND fte <= 1",
            name="check_valid_tenure_fte"
        ),
        db.CheckConstraint(
            "end_date IS NULL OR end_date > start_date",
            name="check_valid_tenure_dates"
        ),
    )

    tenure_id = db.Column(
        db.String(30),
        primary_key=True
    )

    employee_id = db.Column(
        db.String(20),
        db.ForeignKey("employees.employee_id"),
        nullable=False
    )

    start_date = db.Column(
        db.Date,
        nullable=False
    )

    end_date = db.Column(
        db.Date,
        nullable=True
    )

    tenure_type = db.Column(
        db.String(30),
        nullable=False
    )

    fte = db.Column(
        db.Float,
        nullable=False,
        default=1.0
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    def __repr__(self):
        return f"<Tenure {self.tenure_id}>"
