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
    ProposalHistory,
)


def money(value):
    return Decimal(str(value)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


def get_proposal(proposal_id):
    proposal = AdjustmentProposal.query.filter_by(
        proposal_id=proposal_id
    ).first()
    if not proposal:
        raise ValueError("Proposal not found.")
    return proposal


def validate_user(name, field_name):
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"{field_name} is required.")
    return name.strip()


def update_proposal_status(proposal, new_status, changed_by, remarks, action):
    old_status = proposal.status
    proposal.status = new_status

    if new_status == "APPROVED":
        proposal.approved_by = changed_by
        proposal.approved_at = datetime.now(timezone.utc)
    elif new_status == "REJECTED":
        proposal.rejected_by = changed_by
        proposal.rejected_at = datetime.now(timezone.utc)

    db.session.add(ProposalHistory(
        proposal_id=proposal.proposal_id,
        previous_status=old_status,
        new_status=new_status,
        changed_by=changed_by,
        remarks=remarks,
    ))
    db.session.add(AuditLog(
        entity_type="ADJUSTMENT_PROPOSAL",
        entity_id=proposal.proposal_id,
        action=action,
        old_value=json.dumps({"status": old_status}),
        new_value=json.dumps({"status": new_status}),
        performed_by=changed_by,
        remarks=remarks,
    ))


def submit_proposal(proposal_id, submitted_by, remarks):
    try:
        proposal = get_proposal(proposal_id)
        submitted_by = validate_user(submitted_by, "Submitted by name")
        if not isinstance(remarks, str) or not remarks.strip():
            raise ValueError("Submission remarks are required.")
        if proposal.status != "DRAFT":
            raise ValueError("Only DRAFT proposals can be submitted.")

        update_proposal_status(
            proposal, "SUBMITTED", submitted_by, remarks.strip(), "UPDATE"
        )
        db.session.commit()
        return {
            "success": True,
            "proposal_id": proposal_id,
            "status": proposal.status,
            "message": "Proposal submitted successfully for HR review.",
        }
    except Exception:
        db.session.rollback()
        raise


def approve_proposal(proposal_id, approved_by, remarks):
    try:
        proposal = get_proposal(proposal_id)
        approved_by = validate_user(approved_by, "Approver name")
        if not isinstance(remarks, str) or not remarks.strip():
            raise ValueError("Approval remarks are required.")
        if proposal.status != "SUBMITTED":
            raise ValueError("Only SUBMITTED proposals can be approved.")

        update_proposal_status(
            proposal, "APPROVED", approved_by, remarks.strip(), "APPROVE"
        )
        db.session.commit()
        return {
            "success": True,
            "proposal_id": proposal_id,
            "status": proposal.status,
            "message": "Proposal approved successfully.",
        }
    except Exception:
        db.session.rollback()
        raise


def reject_proposal(proposal_id, rejected_by, remarks):
    try:
        proposal = get_proposal(proposal_id)
        rejected_by = validate_user(rejected_by, "Reviewer name")
        if not isinstance(remarks, str) or not remarks.strip():
            raise ValueError("Rejection reason is required.")
        if proposal.status != "SUBMITTED":
            raise ValueError("Only SUBMITTED proposals can be rejected.")

        update_proposal_status(
            proposal, "REJECTED", rejected_by, remarks.strip(), "REJECT"
        )
        db.session.commit()
        return {
            "success": True,
            "proposal_id": proposal_id,
            "status": proposal.status,
            "message": "Proposal rejected successfully.",
        }
    except Exception:
        db.session.rollback()
        raise


def verify_approval_history(proposal):
    if (
        proposal.status != "APPROVED"
        or not proposal.approved_by
        or not proposal.approved_at
    ):
        raise ValueError("Proposal approval details are missing.")

    history = ProposalHistory.query.filter_by(
        proposal_id=proposal.proposal_id,
        previous_status="SUBMITTED",
        new_status="APPROVED",
        changed_by=proposal.approved_by,
    ).first()
    if not history or not isinstance(history.remarks, str) or not history.remarks.strip():
        raise ValueError(
            "Valid approval history not found. Proposal must pass the approval workflow."
        )


def validate_current_compensation(proposal, employee, today):
    if employee.employment_status != "ACTIVE":
        raise ValueError("Only ACTIVE employees can receive adjustments.")

    current_salary = SalaryRecord.query.filter_by(
        salary_id=proposal.current_salary_id
    ).first()
    if not current_salary:
        raise ValueError("Current salary record not found.")
    if current_salary.employee_id != employee.employee_id:
        raise ValueError("Salary record does not belong to employee.")
    if current_salary.currency_code != proposal.currency_code:
        raise ValueError("Currency mismatch.")
    if current_salary.effective_from is None or current_salary.effective_from > today:
        raise ValueError("Current salary is not effective yet.")
    if current_salary.effective_to is not None and current_salary.effective_to <= today:
        raise ValueError("Current salary record is no longer active.")

    active_salaries = SalaryRecord.query.filter(
        SalaryRecord.employee_id == employee.employee_id,
        SalaryRecord.effective_from <= today,
        or_(
            SalaryRecord.effective_to.is_(None),
            SalaryRecord.effective_to > today,
        ),
    ).all()
    if len(active_salaries) != 1:
        raise ValueError("Employee must have exactly one active salary record.")
    if active_salaries[0].salary_id != current_salary.salary_id:
        raise ValueError(
            "Proposal does not reference the employee's active salary."
        )

    current_fte = Decimal(str(current_salary.fte))
    if not current_fte.is_finite() or current_fte <= 0 or current_fte > 1:
        raise ValueError("Invalid employee FTE value.")

    band = CompensationBand.query.filter_by(
        band_id=current_salary.band_id
    ).first()
    if not band:
        raise ValueError("Compensation band not found.")
    if band.effective_from is None or band.effective_from > today:
        raise ValueError("Compensation band is not effective yet.")
    if band.effective_to is not None and band.effective_to <= today:
        raise ValueError("Compensation band is no longer effective.")
    if (
        band.role_id != employee.role_id
        or band.level_id != employee.level_id
        or band.location_id != employee.location_id
    ):
        raise ValueError(
            "Employee role, level, or location does not match compensation band."
        )
    if band.currency_code != proposal.currency_code:
        raise ValueError("Compensation band currency mismatch.")

    band_min = money(band.min_salary)
    band_mid = money(band.midpoint_salary)
    band_max = money(band.max_salary)
    if not (Decimal("0") < band_min < band_mid < band_max):
        raise ValueError("Invalid compensation band salary range.")

    return current_salary, current_fte, band


def apply_proposal(proposal_id, applied_by):
    try:
        proposal = get_proposal(proposal_id)
        applied_by = validate_user(applied_by, "Applied by name")

        if proposal.status != "APPROVED":
            raise ValueError("Only APPROVED proposals can be applied.")
        verify_approval_history(proposal)

        employee = Employee.query.filter_by(
            employee_id=proposal.employee_id
        ).first()
        if not employee:
            raise ValueError("Employee not found.")

        today = date.today()
        current_salary, current_fte, band = validate_current_compensation(
            proposal, employee, today
        )

        proposed_full_time_salary = money(proposal.proposed_salary)
        if proposed_full_time_salary <= 0:
            raise ValueError("Proposed salary must be greater than zero.")
        if not (
            money(band.min_salary)
            <= proposed_full_time_salary
            <= money(band.max_salary)
        ):
            raise ValueError("Proposed salary must be within the compensation band.")

        current_full_time_salary = money(
            Decimal(str(current_salary.base_salary)) / current_fte
        )
        if proposed_full_time_salary <= current_full_time_salary:
            raise ValueError(
                "Proposed salary must be higher than current FTE-normalized salary."
            )

        actual_proposed_salary = money(
            proposed_full_time_salary * current_fte
        )
        new_salary_id = (
            f"SAL-{proposal.employee_id}-ADJ-{proposal.proposal_id[-8:]}"
        )
        if SalaryRecord.query.filter_by(salary_id=new_salary_id).first():
            raise ValueError("New salary record already exists.")

        old_status = proposal.status
        old_salary_value = str(current_salary.base_salary)
        current_salary.effective_to = today

        new_salary = SalaryRecord(
            salary_id=new_salary_id,
            employee_id=proposal.employee_id,
            band_id=current_salary.band_id,
            base_salary=actual_proposed_salary,
            currency_code=proposal.currency_code,
            fte=current_salary.fte,
            effective_from=today,
            effective_to=None,
            change_reason=f"Approved adjustment: {proposal.proposal_id}",
        )
        db.session.add(new_salary)

        proposal.status = "APPLIED"
        proposal.applied_at = datetime.now(timezone.utc)

        db.session.add(ProposalHistory(
            proposal_id=proposal.proposal_id,
            previous_status=old_status,
            new_status="APPLIED",
            changed_by=applied_by,
            remarks=f"New salary record created: {new_salary_id}",
        ))
        db.session.add(AuditLog(
            entity_type="ADJUSTMENT_PROPOSAL",
            entity_id=proposal.proposal_id,
            action="APPLY",
            old_value=json.dumps({
                "status": old_status,
                "salary_id": current_salary.salary_id,
                "salary": old_salary_value,
            }),
            new_value=json.dumps({
                "status": "APPLIED",
                "salary_id": new_salary_id,
                "salary": str(actual_proposed_salary),
                "fte": str(current_fte),
            }),
            performed_by=applied_by,
            remarks="Approved salary adjustment applied.",
        ))

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
            "status": "APPLIED",
        }
    except Exception:
        db.session.rollback()
        raise
