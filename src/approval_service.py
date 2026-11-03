
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import json

from sqlalchemy import or_

from extensions import db

from models import (
    AdjustmentProposal,
    SalaryRecord,
    Employee,
    CompensationBand,
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
# COMMON VALIDATIONS
# --------------------------------------------------

def get_proposal(proposal_id):

    proposal = AdjustmentProposal.query.filter_by(
        proposal_id=proposal_id
    ).with_for_update().first()

    if not proposal:
        raise ValueError("Proposal not found.")

    return proposal


def validate_user(name, field_name):

    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"{field_name} is required.")

    return name.strip()


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

        if not isinstance(remarks, str) or not remarks.strip():
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

        if not isinstance(remarks, str) or not remarks.strip():
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

        if not isinstance(remarks, str) or not remarks.strip():
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
# VERIFY APPROVAL HISTORY
# --------------------------------------------------

def verify_approval_history(proposal):

    if proposal.status != "APPROVED":
        raise ValueError(
            "Only APPROVED proposals can be applied."
        )

    if not proposal.approved_by or not proposal.approved_by.strip():
        raise ValueError(
            "Proposal approval attribution is missing."
        )

    if not proposal.approved_at:
        raise ValueError(
            "Proposal approval timestamp is missing."
        )

    approval_history = ProposalHistory.query.filter_by(
        proposal_id=proposal.proposal_id,
        previous_status="SUBMITTED",
        new_status="APPROVED",
        changed_by=proposal.approved_by
    ).order_by(
        ProposalHistory.changed_at.desc()
    ).first()

    if not approval_history:
        raise ValueError(
            "Valid approval history was not found. "
            "Proposal cannot be applied."
        )

    if not approval_history.changed_at:
        raise ValueError(
            "Approval history timestamp is missing."
        )

    if not approval_history.remarks or not approval_history.remarks.strip():
        raise ValueError(
            "Approval history remarks are missing."
        )

    if approval_history.changed_at.date() != proposal.approved_at.date():
        raise ValueError(
            "Approval timestamp does not match approval history."
        )

    return approval_history


# --------------------------------------------------
# VERIFY CURRENT SALARY AND COMPENSATION BAND
# --------------------------------------------------

def validate_current_compensation(
    employee,
    current_salary,
    proposal,
    effective_date
):

    if employee.employment_status != "ACTIVE":
        raise ValueError(
            "Only ACTIVE employees are eligible for salary adjustments."
        )

    if current_salary.employee_id != employee.employee_id:
        raise ValueError(
            "Salary record does not belong to this employee."
        )

    if (
        current_salary.currency_code.strip().upper()
        != proposal.currency_code.strip().upper()
    ):
        raise ValueError("Proposal and salary currencies do not match.")

    if current_salary.effective_from >= effective_date:
        raise ValueError(
            "Current salary record has an invalid start date."
        )

    if (
        current_salary.effective_to is not None
        and current_salary.effective_to <= effective_date
    ):
        raise ValueError(
            "Referenced salary record is no longer active."
        )

    # Ensure the referenced salary is the employee's
    # only currently active salary record.

    active_salary_records = SalaryRecord.query.filter(
        SalaryRecord.employee_id == employee.employee_id,
        SalaryRecord.effective_from <= effective_date,
        or_(
            SalaryRecord.effective_to.is_(None),
            SalaryRecord.effective_to > effective_date
        )
    ).all()

    if len(active_salary_records) != 1:
        raise ValueError(
            "Employee has missing or overlapping active salary records."
        )

    if active_salary_records[0].salary_id != current_salary.salary_id:
        raise ValueError(
            "Employee's current salary has changed. "
            "Proposal requires re-review."
        )

    # Validate FTE.

    current_fte = Decimal(str(current_salary.fte))

    if current_fte <= 0 or current_fte > 1:
        raise ValueError("Invalid employee FTE value.")

    # Fetch the linked compensation band.

    band = CompensationBand.query.filter_by(
        band_id=current_salary.band_id
    ).first()

    if not band:
        raise ValueError("Compensation band was not found.")

    # Validate band effective dates.

    if band.effective_from > effective_date:
        raise ValueError("Compensation band is not yet effective.")

    if (
        band.effective_to is not None
        and band.effective_to <= effective_date
    ):
        raise ValueError("Compensation band has expired.")

    # Validate employee assignment against band.

    if (
        band.role_id != employee.role_id
        or band.level_id != employee.level_id
        or band.location_id != employee.location_id
    ):
        raise ValueError(
            "Employee role, level or location has changed. "
            "Proposal requires re-review."
        )

    # Validate currency.

    if (
        band.currency_code.strip().upper()
        != proposal.currency_code.strip().upper()
    ):
        raise ValueError(
            "Proposal currency does not match compensation band currency."
        )

    # Validate band range.

    minimum = money(band.min_salary)
    midpoint = money(band.midpoint_salary)
    maximum = money(band.max_salary)

    if not (minimum > 0 and minimum < midpoint < maximum):
        raise ValueError("Compensation band range is invalid.")

    return band, current_fte, minimum, maximum


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

        # 1. Verify genuine approval.

        verify_approval_history(proposal)

        # 2. Fetch employee.

        employee = Employee.query.filter_by(
            employee_id=proposal.employee_id
        ).first()

        if not employee:
            raise ValueError("Employee not found.")

        # 3. Fetch referenced salary.

        current_salary = SalaryRecord.query.filter_by(
            salary_id=proposal.current_salary_id
        ).first()

        if not current_salary:
            raise ValueError("Current salary record not found.")

        effective_date = date.today()

        # 4. Revalidate salary, FTE and compensation band.

        band, current_fte, minimum, maximum = (
            validate_current_compensation(
                employee,
                current_salary,
                proposal,
                effective_date
            )
        )

        # 5. Proposal salary is FTE-normalized.

        proposed_full_time_salary = money(
            proposal.proposed_salary
        )

        current_full_time_salary = money(
            Decimal(str(current_salary.base_salary))
            / current_fte
        )

        if proposed_full_time_salary <= current_full_time_salary:
            raise ValueError(
                "Proposed salary must exceed current FTE-normalized salary."
            )

        # 6. Ensure proposed salary remains inside band.

        if not (
            minimum <= proposed_full_time_salary <= maximum
        ):
            raise ValueError(
                "Proposed salary is outside the current compensation band. "
                "Proposal requires re-review."
            )

        # 7. Convert normalized salary to actual salary.

        actual_proposed_salary = money(
            proposed_full_time_salary * current_fte
        )

        # 8. Prevent duplicate salary creation.

        new_salary_id = (
            f"SAL-{proposal.employee_id}-ADJ-"
            f"{proposal.proposal_id[-8:]}"
        )

        existing_salary = SalaryRecord.query.filter_by(
            salary_id=new_salary_id
        ).first()

        if existing_salary:
            raise ValueError(
                "Salary record for this proposal already exists."
            )

        # 9. Close existing salary.

        old_salary_value = money(current_salary.base_salary)

        current_salary.effective_to = effective_date

        # 10. Create new salary record.

        new_salary = SalaryRecord(
            salary_id=new_salary_id,
            employee_id=proposal.employee_id,
            band_id=band.band_id,
            base_salary=actual_proposed_salary,
            currency_code=proposal.currency_code,
            fte=float(current_fte),
            effective_from=effective_date,
            effective_to=None,
            change_reason=(
                f"Approved compensation adjustment: "
                f"{proposal.proposal_id}"
            )
        )

        db.session.add(new_salary)

        # 11. Update proposal status.

        old_status = proposal.status

        proposal.status = "APPLIED"
        proposal.applied_at = datetime.now(timezone.utc)

        # 12. Record proposal history.

        history = ProposalHistory(
            proposal_id=proposal.proposal_id,
            previous_status=old_status,
            new_status="APPLIED",
            changed_by=applied_by,
            remarks=(
                f"Approved adjustment applied. "
                f"New salary record: {new_salary_id}"
            )
        )

        # 13. Record audit log.

        audit = AuditLog(
            entity_type="ADJUSTMENT_PROPOSAL",
            entity_id=proposal.proposal_id,
            action="APPLY",
            old_value=json.dumps({
                "status": old_status,
                "salary_id": current_salary.salary_id,
                "salary": str(old_salary_value)
            }),
            new_value=json.dumps({
                "status": "APPLIED",
                "salary_id": new_salary_id,
                "salary": str(actual_proposed_salary),
                "normalized_salary": str(proposed_full_time_salary),
                "fte": str(current_fte),
                "currency_code": proposal.currency_code,
                "band_id": band.band_id
            }),
            performed_by=applied_by,
            remarks="Approved salary adjustment applied."
        )

        db.session.add(history)
        db.session.add(audit)

        # 14. Commit everything together.

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
