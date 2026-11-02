
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


# --------------------------------------------------
# COMPVISTA HR APPROVAL WORKFLOW
# --------------------------------------------------

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
        raise ValueError(
            f"Proposal {proposal_id} was not found."
        )

    return proposal


# --------------------------------------------------
# COMMON STATUS CHANGE FUNCTION
# --------------------------------------------------

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
        old_value=json.dumps({
            "status": old_status
        }),
        new_value=json.dumps({
            "status": new_status
        }),
        performed_by=changed_by,
        remarks=remarks
    )

    db.session.add(history)
    db.session.add(audit)


# --------------------------------------------------
# 1. APPROVE PROPOSAL
# --------------------------------------------------

def approve_proposal(
    proposal_id,
    approved_by,
    remarks
):
    try:

        proposal = get_proposal(proposal_id)

        if proposal.status != "DRAFT":
            raise ValueError(
                "Only DRAFT proposals can be approved."
            )

        if not approved_by or not approved_by.strip():
            raise ValueError(
                "Approver name is required."
            )

        if not remarks or not remarks.strip():
            raise ValueError(
                "Approval remarks are required."
            )

        update_proposal_status(
            proposal=proposal,
            new_status="APPROVED",
            changed_by=approved_by.strip(),
            remarks=remarks.strip(),
            action="APPROVE"
        )

        db.session.commit()

        return {
            "success": True,
            "message": "Proposal approved successfully.",
            "proposal_id": proposal_id,
            "status": proposal.status
        }

    except Exception:
        db.session.rollback()
        raise


# --------------------------------------------------
# 2. REJECT PROPOSAL
# --------------------------------------------------

def reject_proposal(
    proposal_id,
    rejected_by,
    remarks
):
    try:

        proposal = get_proposal(proposal_id)

        if proposal.status != "DRAFT":
            raise ValueError(
                "Only DRAFT proposals can be rejected."
            )

        if not rejected_by or not rejected_by.strip():
            raise ValueError(
                "Reviewer name is required."
            )

        if not remarks or not remarks.strip():
            raise ValueError(
                "Rejection reason is required."
            )

        update_proposal_status(
            proposal=proposal,
            new_status="REJECTED",
            changed_by=rejected_by.strip(),
            remarks=remarks.strip(),
            action="REJECT"
        )

        db.session.commit()

        return {
            "success": True,
            "message": "Proposal rejected successfully.",
            "proposal_id": proposal_id,
            "status": proposal.status
        }

    except Exception:
        db.session.rollback()
        raise


# --------------------------------------------------
# 3. APPLY APPROVED PROPOSAL
# --------------------------------------------------

def apply_proposal(
    proposal_id,
    applied_by
):
    try:

        proposal = get_proposal(proposal_id)

        if proposal.status != "APPROVED":
            raise ValueError(
                "Only APPROVED proposals can be applied."
            )

        if not applied_by or not applied_by.strip():
            raise ValueError(
                "Applied by name is required."
            )

        employee = Employee.query.filter_by(
            employee_id=proposal.employee_id
        ).first()

        if not employee:
            raise ValueError(
                "Employee record was not found."
            )

        current_salary = SalaryRecord.query.filter_by(
            salary_id=proposal.current_salary_id
        ).first()

        if not current_salary:
            raise ValueError(
                "Current salary record was not found."
            )

        if current_salary.employee_id != proposal.employee_id:
            raise ValueError(
                "Salary record does not belong to this employee."
            )

        if current_salary.currency_code != proposal.currency_code:
            raise ValueError(
                "Proposal and salary currencies do not match."
            )

        if money(proposal.proposed_salary) <= money(current_salary.base_salary):
            raise ValueError(
                "Proposed salary must exceed the current salary."
            )

        effective_date = date.today()

        if current_salary.effective_from >= effective_date:
            raise ValueError(
                "Cannot apply a salary change before the current "
                "salary record has started."
            )

        if (
            current_salary.effective_to is not None
            and current_salary.effective_to <= effective_date
        ):
            raise ValueError(
                "The referenced salary record is no longer active."
            )

        # Close the existing salary record.
        current_salary.effective_to = effective_date

        # Create a new salary record.
        new_salary_id = (
            f"SAL-{proposal.employee_id}-ADJ-"
            f"{proposal.proposal_id[-8:]}"
        )

        existing_new_salary = SalaryRecord.query.filter_by(
            salary_id=new_salary_id
        ).first()

        if existing_new_salary:
            raise ValueError(
                "A salary record for this proposal already exists."
            )

        new_salary = SalaryRecord(
            salary_id=new_salary_id,
            employee_id=proposal.employee_id,
            band_id=current_salary.band_id,
            base_salary=money(proposal.proposed_salary),
            currency_code=proposal.currency_code,
            fte=current_salary.fte,
            effective_from=effective_date,
            effective_to=None,
            change_reason=(
                f"Approved compensation adjustment: "
                f"{proposal.proposal_id}"
            )
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
            remarks=(
                f"Approved adjustment applied. "
                f"New salary record: {new_salary_id}"
            )
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
            "message": "Approved salary adjustment applied successfully.",
            "proposal_id": proposal_id,
            "new_salary_id": new_salary_id,
            "new_salary": str(proposal.proposed_salary),
            "currency_code": proposal.currency_code,
            "status": proposal.status
        }

    except Exception:
        db.session.rollback()
        raise

