
from extensions import db


class EmployeeLocationHistory(db.Model):
    __tablename__ = "employee_location_history"

    __table_args__ = (
        db.CheckConstraint(
            "effective_to IS NULL OR effective_to > effective_from",
            name="check_valid_location_history_dates"
        ),
    )

    history_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    employee_id = db.Column(
        db.String(20),
        db.ForeignKey("employees.employee_id"),
        nullable=False
    )

    location_id = db.Column(
        db.Integer,
        db.ForeignKey("locations.location_id"),
        nullable=False
    )

    effective_from = db.Column(
        db.Date,
        nullable=False
    )

    effective_to = db.Column(
        db.Date,
        nullable=True
    )

    change_reason = db.Column(
        db.String(200),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    def __repr__(self):
        return (
            f"<EmployeeLocationHistory "
            f"{self.employee_id} - {self.location_id}>"
        )
