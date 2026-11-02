
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
import json

from extensions import db

from models import (
    AdjustmentProposal,
    SalaryRecord,
    Employee,
    AuditLog,
    ProposalHistory
)


def money(value):
    return Decimal(str(value)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )


def get_proposal(proposal_id):
    proposal = AdjustmentProposal.query.filter_by(
        proposal_id=proposal_id
    ).first()

    if not proposal:
        raise ValueError("Proposal not found.")

    return proposal


def update_proposal_status(
    proposal,
    new_status,
    changed_by,
    remarks,
    action
):
    old_status = proposal.status

    proposal.status = new_status

    if new_status == "APPROVED":
        proposal.approved_by = changed_by
        proposal.approved_at = datetime.utcnow()

    history = ProposalHistory(
        proposal_id=proposal.proposal_id,
        previous_status=old_status,
        new_status=new_status,
        changed_by=changed_by,
        remarks=remarks
    )

    audit = AuditLog(
        entity_type="ADJUSTMENT_PROPOSAL",
        entity_id=proposal.proposal_id,
        action=action,
        old_value=json.dumps({"status": old_status}),
        new_value=json.dumps({"status": new_status}),
        performed_by=changed_by,
        remarks=remarks
    )

    db.session.add(history)
    db.session.add(audit)


# --------------------------------------------------
# APPROVE PROPOSAL
# --------------------------------------------------

def approve_proposal(proposal_id, approved_by, remarks):

    try:
        proposal = get_proposal(proposal_id)

        if proposal.status != "DRAFT":
            raise ValueError("Only DRAFT proposals can be approved.")

        if not approved_by or not approved_by.strip():
            raise ValueError("Approver name is required.")

        if not remarks or not remarks.strip():
            raise ValueError("Approval remarks are required.")

        update_proposal_status(
            proposal,
            "APPROVED",
            approved_by.strip(),
            remarks.strip(),
            "APPROVE"
        )

        db.session.commit()

        return {
            "success": True,
            "proposal_id": proposal_id,
            "status": proposal.status,
            "message": "Proposal approved successfully."
        }

    except Exception:
        db.session.rollback()
        raise


# --------------------------------------------------
# REJECT PROPOSAL
# --------------------------------------------------

def reject_proposal(proposal_id, rejected_by, remarks):

    try:
        proposal = get_proposal(proposal_id)

        if proposal.status != "DRAFT":
            raise ValueError("Only DRAFT proposals can be rejected.")

        if not rejected_by or not rejected_by.strip():
            raise ValueError("Reviewer name is required.")

        if not remarks or not remarks.strip():
            raise ValueError("Rejection reason is required.")

        update_proposal_status(
            proposal,
            "REJECTED",
            rejected_by.strip(),
            remarks.strip(),
            "REJECT"
        )

        db.session.commit()

        return {
            "success": True,
            "proposal_id": proposal_id,
            "status": proposal.status,
            "message": "Proposal rejected successfully."
        }

    except Exception:
        db.session.rollback()
        raise


# --------------------------------------------------
# APPLY APPROVED PROPOSAL
# --------------------------------------------------

def apply_proposal(proposal_id, applied_by):

    try:
        proposal = get_proposal(proposal_id)

        if proposal.status != "APPROVED":
            raise ValueError("Only APPROVED proposals can be applied.")

        if not applied_by or not applied_by.strip():
            raise ValueError("Applied by name is required.")

        employee = Employee.query.filter_by(
            employee_id=proposal.employee_id
        ).first()

        if not employee:
            raise ValueError("Employee not found.")

        current_salary = SalaryRecord.query.filter_by(
            salary_id=proposal.current_salary_id
        ).first()

        if not current_salary:
            raise ValueError("Current salary record not found.")

        if current_salary.employee_id != proposal.employee_id:
            raise ValueError("Salary record does not belong to employee.")

        if current_salary.currency_code != proposal.currency_code:
            raise ValueError("Currency mismatch.")

        if money(proposal.proposed_salary) <= money(current_salary.base_salary):
            raise ValueError("Proposed salary must be higher than current salary.")

        effective_date = date.today()

        if current_salary.effective_from >= effective_date:
            raise ValueError("Current salary record has an invalid start date.")

        if (
            current_salary.effective_to is not None
            and current_salary.effective_to <= effective_date
        ):
            raise ValueError("Current salary record is no longer active.")

        new_salary_id = (
            f"SAL-{proposal.employee_id}-ADJ-"
            f"{proposal.proposal_id[-8:]}"
        )

        if SalaryRecord.query.filter_by(
            salary_id=new_salary_id
        ).first():
            raise ValueError("New salary record already exists.")

        # Close the previous salary record.
        current_salary.effective_to = effective_date

        # Create a new salary record.
        new_salary = SalaryRecord(
            salary_id=new_salary_id,
            employee_id=proposal.employee_id,
            band_id=current_salary.band_id,
            base_salary=money(proposal.proposed_salary),
            currency_code=proposal.currency_code,
            fte=current_salary.fte,
            effective_from=effective_date,
            effective_to=None,
            change_reason=f"Approved adjustment: {proposal.proposal_id}"
        )

        db.session.add(new_salary)

        old_status = proposal.status
        proposal.status = "APPLIED"
        proposal.applied_at = datetime.utcnow()

        history = ProposalHistory(
            proposal_id=proposal.proposal_id,
            previous_status=old_status,
            new_status="APPLIED",
            changed_by=applied_by.strip(),
            remarks=f"New salary record created: {new_salary_id}"
        )

        audit = AuditLog(
            entity_type="ADJUSTMENT_PROPOSAL",
            entity_id=proposal.proposal_id,
            action="APPLY",
            old_value=json.dumps({
                "status": old_status,
                "salary_id": current_salary.salary_id,
                "salary": str(current_salary.base_salary)
            }),
            new_value=json.dumps({
                "status": "APPLIED",
                "salary_id": new_salary_id,
                "salary": str(proposal.proposed_salary)
            }),
            performed_by=applied_by.strip(),
            remarks="Approved salary adjustment applied."
        )

        db.session.add(history)
        db.session.add(audit)

        db.session.commit()

        return {
            "success": True,
            "message": "Salary adjustment applied successfully.",
            "proposal_id": proposal_id,
            "new_salary_id": new_salary_id,
            "new_salary": str(proposal.proposed_salary),
            "currency_code": proposal.currency_code,
            "status": "APPLIED"
        }

    except Exception:
        db.session.rollback()
        raise
