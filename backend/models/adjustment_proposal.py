
from extensions import db
from sqlalchemy import Numeric


class AdjustmentProposal(db.Model):
    __tablename__ = "adjustment_proposals"

    __table_args__ = (
        db.CheckConstraint(
            "proposed_salary > 0",
            name="check_positive_proposed_salary"
        ),
        db.CheckConstraint(
            "status IN ('DRAFT', 'SUBMITTED', 'APPROVED', 'REJECTED', 'APPLIED')",
            name="check_valid_proposal_status"
        ),
    )

    proposal_id = db.Column(
        db.String(30),
        primary_key=True
    )

    employee_id = db.Column(
        db.String(20),
        db.ForeignKey("employees.employee_id"),
        nullable=False
    )

    current_salary_id = db.Column(
        db.String(30),
        db.ForeignKey("salary_records.salary_id"),
        nullable=False
    )

    proposed_salary = db.Column(
        Numeric(14, 2),
        nullable=False
    )

    currency_code = db.Column(
        db.String(5),
        nullable=False
    )

    reason = db.Column(
        db.Text,
        nullable=False
    )

    issue_type = db.Column(
        db.String(50),
        nullable=False
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="DRAFT"
    )

    proposed_by = db.Column(
        db.String(100),
        nullable=False
    )

    approved_by = db.Column(db.String(100))

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    approved_at = db.Column(db.DateTime)

    rejected_by = db.Column(db.String(100))

    rejected_at = db.Column(db.DateTime)

    applied_at = db.Column(db.DateTime)

    def __repr__(self):
        return f"<AdjustmentProposal {self.proposal_id}>"
