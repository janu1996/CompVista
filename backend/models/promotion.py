
from extensions import db


class Promotion(db.Model):
    __tablename__ = "promotions"

    __table_args__ = (
        db.CheckConstraint(
            "previous_role_id != new_role_id OR previous_level_id != new_level_id",
            name="check_actual_promotion_change"
        ),
    )

    promotion_id = db.Column(
        db.String(30),
        primary_key=True
    )

    employee_id = db.Column(
        db.String(20),
        db.ForeignKey("employees.employee_id"),
        nullable=False
    )

    previous_role_id = db.Column(
        db.Integer,
        db.ForeignKey("roles.role_id"),
        nullable=False
    )

    new_role_id = db.Column(
        db.Integer,
        db.ForeignKey("roles.role_id"),
        nullable=False
    )

    previous_level_id = db.Column(
        db.Integer,
        db.ForeignKey("levels.level_id"),
        nullable=False
    )

    new_level_id = db.Column(
        db.Integer,
        db.ForeignKey("levels.level_id"),
        nullable=False
    )

    promotion_date = db.Column(
        db.Date,
        nullable=False
    )

    reason = db.Column(db.Text)

    approved_by = db.Column(
        db.String(100),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    def __repr__(self):
        return f"<Promotion {self.promotion_id}>"
