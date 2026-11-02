
from extensions import db


class Employee(db.Model):
    __tablename__ = "employees"

    employee_id = db.Column(db.String(20), primary_key=True)

    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(150), unique=True, nullable=False)

    role_id = db.Column(db.Integer, nullable=False)
    level_id = db.Column(db.Integer, nullable=False)
    location_id = db.Column(db.Integer, nullable=False)

    hire_date = db.Column(db.Date, nullable=False)

    employment_status = db.Column(
        db.String(20),
        nullable=False,
        default="ACTIVE"
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    def __repr__(self):
        return f"<Employee {self.employee_id}>"
