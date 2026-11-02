
from extensions import db


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    __table_args__ = (
        db.CheckConstraint(
            "action IN ('CREATE', 'UPDATE', 'DELETE', 'APPROVE', 'REJECT', 'APPLY')",
            name="check_valid_audit_action"
        ),
    )

    audit_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    entity_type = db.Column(
        db.String(50),
        nullable=False
    )

    entity_id = db.Column(
        db.String(50),
        nullable=False
    )

    action = db.Column(
        db.String(30),
        nullable=False
    )

    old_value = db.Column(db.Text)

    new_value = db.Column(db.Text)

    performed_by = db.Column(
        db.String(100),
        nullable=False
    )

    performed_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    remarks = db.Column(db.Text)

    def __repr__(self):
        return f"<AuditLog {self.audit_id}>"
