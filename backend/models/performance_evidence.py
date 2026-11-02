
from extensions import db


class PerformanceEvidence(db.Model):
    __tablename__ = "performance_evidence"

    __table_args__ = (
        db.CheckConstraint(
            "performance_rating >= 1 AND performance_rating <= 5",
            name="check_valid_performance_rating"
        ),
    )

    evidence_id = db.Column(
        db.String(30),
        primary_key=True
    )

    employee_id = db.Column(
        db.String(20),
        db.ForeignKey("employees.employee_id"),
        nullable=False
    )

    review_period = db.Column(
        db.String(30),
        nullable=False
    )

    performance_rating = db.Column(
        db.Float,
        nullable=False
    )

    rating_scale = db.Column(
        db.String(30),
        nullable=False,
        default="1-5"
    )

    evidence_type = db.Column(
        db.String(50),
        nullable=False
    )

    description = db.Column(db.Text)

    recorded_by = db.Column(
        db.String(100)
    )

    recorded_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    def __repr__(self):
        return f"<PerformanceEvidence {self.evidence_id}>"
