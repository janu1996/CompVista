
from datetime import date, datetime, timezone
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
# MONEY HELPER
# --------------------------------------------------

def money(value):
    return Decimal(str(value)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )


# --------------------------------------------------
# GET PROPOSAL
# --------------------------------------------------

def get_proposal(proposal_id):

    proposal = AdjustmentProposal.query.filter_by(
        proposal_id=proposal_id
    ).first()

    if not proposal:
        raise ValueError("Proposal not found.")

    return proposal


# --------------------------------------------------
# VALIDATE USER INPUT
# --------------------------------------------------

def validate_user(name, field_name):

    if not name or not name.strip():
        raise ValueError(f"{field_name} is required.")

    return name.strip()


# --------------------------------------------------
# UPDATE PROPOSAL STATUS
# --------------------------------------------------

def update_proposal_status(
    proposal,
    new_status,
    changed_by,
    remarks,
    action
):

    old_status = proposal.status
    current_time = datetime.now(timezone.utc)

    proposal.status = new_status

    if new_status == "APPROVED":
        proposal.approved_by = changed_by
        proposal.approved_at = current_time

    elif new_status == "REJECTED":
        proposal.rejected_by = changed_by
        proposal.rejected_at = current_time

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
# SUBMIT PROPOSAL
# DRAFT -> SUBMITTED
# --------------------------------------------------

def submit_proposal(proposal_id, submitted_by, remarks):

    try:

        proposal = get_proposal(proposal_id)

        submitted_by = validate_user(
            submitted_by,
            "Submitted by name"
        )

        if not remarks or not remarks.strip():
            raise ValueError("Submission remarks are required.")

        if proposal.status != "DRAFT":
            raise ValueError(
                "Only DRAFT proposals can be submitted."
            )

        update_proposal_status(
            proposal,
            "SUBMITTED",
            submitted_by,
            remarks.strip(),
            "UPDATE"
        )

        db.session.commit()

        return {
            "success": True,
            "proposal_id": proposal_id,
            "status": proposal.status,
            "message": "Proposal submitted successfully for HR review."
        }

    except Exception:
        db.session.rollback()
        raise


# --------------------------------------------------
# APPROVE PROPOSAL
# SUBMITTED -> APPROVED
# --------------------------------------------------

def approve_proposal(proposal_id, approved_by, remarks):

    try:

        proposal = get_proposal(proposal_id)

        approved_by = validate_user(
            approved_by,
            "Approver name"
        )

        if not remarks or not remarks.strip():
            raise ValueError("Approval remarks are required.")

        if proposal.status != "SUBMITTED":
            raise ValueError(
                "Only SUBMITTED proposals can be approved."
            )

        update_proposal_status(
            proposal,
            "APPROVED",
            approved_by,
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
# SUBMITTED -> REJECTED
# --------------------------------------------------

def reject_proposal(proposal_id, rejected_by, remarks):

    try:

        proposal = get_proposal(proposal_id)

        rejected_by = validate_user(
            rejected_by,
            "Reviewer name"
        )

        if not remarks or not remarks.strip():
            raise ValueError("Rejection reason is required.")

        if proposal.status != "SUBMITTED":
            raise ValueError(
                "Only SUBMITTED proposals can be rejected."
            )

        update_proposal_status(
            proposal,
            "REJECTED",
            rejected_by,
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
# APPROVED -> APPLIED
# --------------------------------------------------

def apply_proposal(proposal_id, applied_by):

    try:

        proposal = get_proposal(proposal_id)

        applied_by = validate_user(
            applied_by,
            "Applied by name"
        )

        if proposal.status != "APPROVED":
            raise ValueError(
                "Only APPROVED proposals can be applied."
            )

        if not proposal.approved_by or not proposal.approved_at:
            raise ValueError(
                "Proposal approval details are missing."
            )

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
            raise ValueError(
                "Salary record does not belong to employee."
            )

        if current_salary.currency_code != proposal.currency_code:
            raise ValueError("Currency mismatch.")

        # Validate FTE.
        current_fte = Decimal(str(current_salary.fte))

        if current_fte <= 0 or current_fte > 1:
            raise ValueError("Invalid employee FTE value.")

        # Proposal salary is normalized to full-time equivalent.
        proposed_full_time_salary = money(
            proposal.proposed_salary
        )

        # Existing salary record stores actual salary based on FTE.
        current_full_time_salary = money(
            Decimal(str(current_salary.base_salary)) / current_fte
        )

        if proposed_full_time_salary <= current_full_time_salary:
            raise ValueError(
                "Proposed salary must be higher than current FTE-normalized salary."
            )

        # Convert normalized proposed salary into actual employee salary.
        actual_proposed_salary = money(
            proposed_full_time_salary * current_fte
        )

        effective_date = date.today()

        if current_salary.effective_from >= effective_date:
            raise ValueError(
                "Current salary record has an invalid start date."
            )

        if (
            current_salary.effective_to is not None
            and current_salary.effective_to <= effective_date
        ):
            raise ValueError(
                "Current salary record is no longer active."
            )

        new_salary_id = (
            f"SAL-{proposal.employee_id}-ADJ-"
            f"{proposal.proposal_id[-8:]}"
        )

        if SalaryRecord.query.filter_by(
            salary_id=new_salary_id
        ).first():

            raise ValueError(
                "New salary record already exists."
            )

        # Close the previous salary record.
        current_salary.effective_to = effective_date

        # Create the new salary record.
        new_salary = SalaryRecord(
            salary_id=new_salary_id,
            employee_id=proposal.employee_id,
            band_id=current_salary.band_id,
            base_salary=actual_proposed_salary,
            currency_code=proposal.currency_code,
            fte=current_salary.fte,
            effective_from=effective_date,
            effective_to=None,
            change_reason=(
                f"Approved adjustment: {proposal.proposal_id}"
            )
        )

        db.session.add(new_salary)

        # Update proposal status.
        old_status = proposal.status

        proposal.status = "APPLIED"
        proposal.applied_at = datetime.now(timezone.utc)

        # Record proposal history.
        history = ProposalHistory(
            proposal_id=proposal.proposal_id,
            previous_status=old_status,
            new_status="APPLIED",
            changed_by=applied_by,
            remarks=f"New salary record created: {new_salary_id}"
        )

        # Record audit details.
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
                "salary": str(actual_proposed_salary),
                "fte": str(current_fte)
            }),
            performed_by=applied_by,
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
            "new_salary": str(actual_proposed_salary),
            "normalized_salary": str(proposed_full_time_salary),
            "fte": str(current_fte),
            "currency_code": proposal.currency_code,
            "status": "APPLIED"
        }

    except Exception:
        db.session.rollback()
        raise
