
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from extensions import db

from models import (
    AdjustmentProposal,
    SalaryRecord,
    AuditLog,
    ProposalHistory
)

from services.proposal_service import generate_adjustment_proposals

from services.approval_service import (
    submit_proposal,
    approve_proposal,
    apply_proposal
)


def create_approved_proposal(proposal_scenario):

    result = generate_adjustment_proposals(
        proposed_by="Pytest"
    )

    proposal_id = result["proposals"][0]["proposal_id"]

    submit_proposal(
        proposal_id=proposal_id,
        submitted_by="Test Submitter",
        remarks="Submitted for approval."
    )

    approve_proposal(
        proposal_id=proposal_id,
        approved_by="Test HR Manager",
        remarks="Approved for salary adjustment."
    )

    return proposal_id


def test_apply_approved_proposal(proposal_scenario):

    proposal_id = create_approved_proposal(proposal_scenario)

    result = apply_proposal(
        proposal_id=proposal_id,
        applied_by="Test HR Administrator"
    )

    assert result["success"] is True
    assert result["status"] == "APPLIED"

    proposal = db.session.get(AdjustmentProposal, proposal_id)

    assert proposal.status == "APPLIED"
    assert proposal.applied_at is not None


def test_salary_records_updated_correctly(proposal_scenario):

    old_salary_id = proposal_scenario["salary"].salary_id

    proposal_id = create_approved_proposal(proposal_scenario)

    result = apply_proposal(
        proposal_id=proposal_id,
        applied_by="Test HR Administrator"
    )

    old_salary = db.session.get(SalaryRecord, old_salary_id)

    new_salary = db.session.get(
        SalaryRecord,
        result["new_salary_id"]
    )

    assert old_salary is not None
    assert old_salary.effective_to is not None

    assert new_salary is not None
    assert new_salary.employee_id == "EMP-TEST-001"
    assert new_salary.currency_code == "INR"
    assert new_salary.fte == 1.0


def test_apply_salary_with_partial_fte(proposal_scenario):

    salary = proposal_scenario["salary"]

    salary.fte = 0.5
    salary.base_salary = Decimal("250000.00")

    db.session.commit()

    proposal = AdjustmentProposal(
        proposal_id="PROP-FTE-TEST",
        employee_id=salary.employee_id,
        current_salary_id=salary.salary_id,
        proposed_salary=Decimal("680000.00"),
        currency_code="INR",
        reason="FTE calculation test",
        issue_type="LOW_COMPA_RATIO",
        status="APPROVED",
        proposed_by="Pytest",
        approved_by="Test HR Manager",
        approved_at=datetime.now(timezone.utc)
    )

    db.session.add(proposal)
    db.session.commit()

    result = apply_proposal(
        proposal_id=proposal.proposal_id,
        applied_by="Test HR Administrator"
    )

    new_salary = db.session.get(
        SalaryRecord,
        result["new_salary_id"]
    )

    # 680000 * 0.5 = 340000

    assert Decimal(str(new_salary.base_salary)) == Decimal("340000.00")
    assert new_salary.fte == 0.5


def test_cannot_apply_draft_proposal(proposal_scenario):

    result = generate_adjustment_proposals(
        proposed_by="Pytest"
    )

    proposal_id = result["proposals"][0]["proposal_id"]

    with pytest.raises(ValueError, match="Only APPROVED"):

        apply_proposal(
            proposal_id=proposal_id,
            applied_by="Test HR Administrator"
        )

    proposal = db.session.get(AdjustmentProposal, proposal_id)

    assert proposal.status == "DRAFT"


def test_apply_creates_audit_and_history(proposal_scenario):

    proposal_id = create_approved_proposal(proposal_scenario)

    apply_proposal(
        proposal_id=proposal_id,
        applied_by="Test HR Administrator"
    )

    history = ProposalHistory.query.filter_by(
        proposal_id=proposal_id
    ).all()

    audit = AuditLog.query.filter_by(
        entity_id=proposal_id
    ).all()

    assert len(history) == 4
    assert history[-1].new_status == "APPLIED"

    assert len(audit) == 4
    assert audit[-1].action == "APPLY"


def test_cannot_apply_same_proposal_twice(proposal_scenario):

    proposal_id = create_approved_proposal(proposal_scenario)

    first_result = apply_proposal(
        proposal_id=proposal_id,
        applied_by="Test HR Administrator"
    )

    assert first_result["status"] == "APPLIED"

    with pytest.raises(ValueError, match="Only APPROVED"):

        apply_proposal(
            proposal_id=proposal_id,
            applied_by="Test HR Administrator"
        )

    assert SalaryRecord.query.count() == 2
