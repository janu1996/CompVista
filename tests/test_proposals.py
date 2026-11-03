
from datetime import date
from decimal import Decimal

from extensions import db
from models import (
    AdjustmentProposal,
    AuditLog,
    ProposalHistory
)
from services.proposal_service import generate_adjustment_proposals


def test_generates_draft_proposal(proposal_scenario):

    result = generate_adjustment_proposals(
        as_of_date=date(2026, 11, 3),
        proposed_by="Pytest"
    )

    assert result["flagged_employees"] == 1
    assert result["proposals_created"] == 1
    assert result["proposals_skipped"] == 0

    proposal = AdjustmentProposal.query.filter_by(
        current_salary_id="SAL-TEST-001"
    ).first()

    assert proposal is not None
    assert proposal.status == "DRAFT"
    assert proposal.currency_code == "INR"


def test_proposed_salary_calculation(proposal_scenario):

    generate_adjustment_proposals(
        as_of_date=date(2026, 11, 3),
        proposed_by="Pytest"
    )

    proposal = AdjustmentProposal.query.filter_by(
        current_salary_id="SAL-TEST-001"
    ).first()

    # 85% of midpoint (800000) = 680000.
    # Peer median for this single employee = 500000.
    # Therefore suggested salary should be 680000.

    assert proposal is not None
    assert Decimal(str(proposal.proposed_salary)) == Decimal("680000.00")


def test_proposal_creates_audit_and_history(proposal_scenario):

    generate_adjustment_proposals(
        as_of_date=date(2026, 11, 3),
        proposed_by="Pytest"
    )

    proposal = AdjustmentProposal.query.filter_by(
        current_salary_id="SAL-TEST-001"
    ).first()

    assert proposal is not None

    history = ProposalHistory.query.filter_by(
        proposal_id=proposal.proposal_id
    ).all()

    audit = AuditLog.query.filter_by(
        entity_id=proposal.proposal_id
    ).all()

    assert len(history) == 1
    assert history[0].new_status == "DRAFT"

    assert len(audit) == 1
    assert audit[0].action == "CREATE"


def test_duplicate_proposal_is_not_created(proposal_scenario):

    first_result = generate_adjustment_proposals(
        as_of_date=date(2026, 11, 3),
        proposed_by="Pytest"
    )

    second_result = generate_adjustment_proposals(
        as_of_date=date(2026, 11, 3),
        proposed_by="Pytest"
    )

    assert first_result["proposals_created"] == 1
    assert second_result["proposals_created"] == 0
    assert second_result["proposals_skipped"] == 1

    assert AdjustmentProposal.query.count() == 1
