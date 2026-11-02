
from extensions import db


class ProposalHistory(db.Model):
    __tablename__ = "proposal_history"

    __table_args__ = (
        db.CheckConstraint(
            "new_status IN ('DRAFT', 'SUBMITTED', 'APPROVED', 'REJECTED', 'APPLIED')",
            name="check_valid_new_proposal_status"
        ),
        db.CheckConstraint(
            "previous_status IS NULL OR previous_status IN ('DRAFT', 'SUBMITTED', 'APPROVED', 'REJECTED', 'APPLIED')",
            name="check_valid_previous_proposal_status"
        ),
    )

    history_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    proposal_id = db.Column(
        db.String(30),
        db.ForeignKey("adjustment_proposals.proposal_id"),
        nullable=False
    )

    previous_status = db.Column(
        db.String(20)
    )

    new_status = db.Column(
        db.String(20),
        nullable=False
    )

    changed_by = db.Column(
        db.String(100),
        nullable=False
    )

    remarks = db.Column(db.Text)

    changed_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    def __repr__(self):
        return f"<ProposalHistory {self.history_id}>"
