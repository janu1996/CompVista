
import json
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from extensions import db

from models import (
    Employee,
    SalaryRecord,
    AdjustmentProposal,
    AuditLog,
    ProposalHistory
)

from services.compensation_analysis import analyze_compensation


# --------------------------------------------------
# COMPVISTA ADJUSTMENT PROPOSAL SERVICE
# --------------------------------------------------

def to_decimal(value):
    return Decimal(str(value or 0))


def round_money(value):
    return to_decimal(value).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )


def create_proposal_id(employee_id, salary_id):
    """
    Create a stable proposal ID.
    The ID must not exceed 30 characters.
    """

    employee_part = employee_id[-8:]
    salary_part = salary_id[-12:]

    return f"PROP-{employee_part}-{salary_part}"


# --------------------------------------------------
# GENERATE ADJUSTMENT PROPOSALS
# --------------------------------------------------

def generate_adjustment_proposals(
    as_of_date=None,
    proposed_by="CompVista Analysis Engine"
):
    """
    Generate DRAFT adjustment proposals for employees
    who have potential compensation review flags.

    Proposal logic:
    1. Employee must have a potential issue.
    2. Proposed salary is based on peer median and
       85% of the compensation band midpoint.
    3. Proposed salary cannot exceed band maximum.
    4. Proposed salary must be higher than current salary.
    5. Existing proposals for the same salary record
       are not duplicated.

    No proposal is automatically approved or applied.
    """

    if as_of_date is None:
        as_of_date = date.today()

    # --------------------------------------------------
    # 1. RUN COMPENSATION ANALYSIS
    # --------------------------------------------------

    analysis = analyze_compensation(
        as_of_date=as_of_date
    )

    analysis_results = analysis["results"]

    created_count = 0
    skipped_count = 0

    created_proposals = []

    # --------------------------------------------------
    # 2. PROCESS FLAGGED EMPLOYEES
    # --------------------------------------------------

    for row in analysis_results:

        if not row["requires_hr_review"]:
            continue

        employee_id = row["employee_id"]
        salary_id = row["salary_id"]

        # --------------------------------------------------
        # 3. CHECK FOR EXISTING PROPOSAL
        # --------------------------------------------------

        existing_proposal = AdjustmentProposal.query.filter_by(
            current_salary_id=salary_id
        ).first()

        if existing_proposal:
            skipped_count += 1
            continue

        # --------------------------------------------------
        # 4. CALCULATE SUGGESTED SALARY
        # --------------------------------------------------

        current_salary = round_money(
            row["normalized_salary"]
        )

        band_midpoint = round_money(
            row["band_midpoint"]
        )

        band_maximum = round_money(
            row["band_maximum"]
        )

        peer_median = round_money(
            row["peer_median_salary"]
        )

        # A reference target of 85% of band midpoint.
        minimum_target = round_money(
            band_midpoint * Decimal("0.85")
        )

        # Use the higher of peer median and 85% midpoint.
        suggested_salary = max(
            peer_median,
            minimum_target
        )

        # Never exceed the compensation band maximum.
        suggested_salary = min(
            suggested_salary,
            band_maximum
        )

        suggested_salary = round_money(
            suggested_salary
        )

        # Do not create a proposal if no increase is indicated.
        if suggested_salary <= current_salary:
            skipped_count += 1
            continue

        # --------------------------------------------------
        # 5. BUILD EXPLANATION
        # --------------------------------------------------

        issue_types = [
            issue["type"]
            for issue in row["potential_issues"]
        ]

        issue_type = ",".join(issue_types)[:50]

        reason = (
            "Compensation review recommended based on "
            f"the following indicators: {', '.join(issue_types)}. "
            f"Current normalized salary: {current_salary}. "
            f"Comparable group median: {peer_median}. "
            f"Compensation band midpoint: {band_midpoint}. "
            f"Suggested normalized salary: {suggested_salary}. "
            f"Compa-ratio: {row['compa_ratio']}%. "
            f"Comparable group size: {row['peer_group_size']}. "
            "This is a system-generated recommendation and "
            "requires independent HR review."
        )

        # --------------------------------------------------
        # 6. CREATE PROPOSAL
        # --------------------------------------------------

        proposal_id = create_proposal_id(
            employee_id,
            salary_id
        )

        proposal = AdjustmentProposal(
            proposal_id=proposal_id,
            employee_id=employee_id,
            current_salary_id=salary_id,
            proposed_salary=suggested_salary,
            currency_code=row["currency_code"],
            reason=reason,
            issue_type=issue_type,
            status="DRAFT",
            proposed_by=proposed_by
        )

        db.session.add(proposal)

        # --------------------------------------------------
        # 7. CREATE PROPOSAL HISTORY
        # --------------------------------------------------

        history = ProposalHistory(
            proposal_id=proposal_id,
            previous_status=None,
            new_status="DRAFT",
            changed_by=proposed_by,
            remarks="Initial proposal generated by CompVista."
        )

        db.session.add(history)

        # --------------------------------------------------
        # 8. CREATE AUDIT LOG
        # --------------------------------------------------

        audit = AuditLog(
            entity_type="ADJUSTMENT_PROPOSAL",
            entity_id=proposal_id,
            action="CREATE",
            old_value=None,
            new_value=json.dumps({
                "employee_id": employee_id,
                "current_salary_id": salary_id,
                "proposed_salary": str(suggested_salary),
                "currency_code": row["currency_code"],
                "status": "DRAFT",
                "issue_type": issue_type
            }),
            performed_by=proposed_by,
            remarks="Draft adjustment proposal generated."
        )

        db.session.add(audit)

        created_proposals.append({
            "proposal_id": proposal_id,
            "employee_id": employee_id,
            "current_salary": str(current_salary),
            "proposed_salary": str(suggested_salary),
            "currency_code": row["currency_code"],
            "issue_type": issue_type,
            "status": "DRAFT"
        })

        created_count += 1

    # --------------------------------------------------
    # 9. COMMIT ALL CHANGES
    # --------------------------------------------------

    try:

        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    # --------------------------------------------------
    # 10. RETURN SUMMARY
    # --------------------------------------------------

    return {
        "message": "Adjustment proposal generation completed.",
        "analysis_date": as_of_date.isoformat(),
        "flagged_employees": sum(
            1 for row in analysis_results
            if row["requires_hr_review"]
        ),
        "proposals_created": created_count,
        "proposals_skipped": skipped_count,
        "proposals": created_proposals
    }
