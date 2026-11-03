
import pytest

from extensions import db

from models import (
    AdjustmentProposal,
    AuditLog,
    ProposalHistory
)

from services.proposal_service import (
    generate_adjustment_proposals
)

from services.approval_service import (
    submit_proposal,
    approve_proposal,
    reject_proposal
)


def create_draft_proposal(proposal_scenario):

    result = generate_adjustment_proposals(
        proposed_by="Pytest"
    )

    assert result["proposals_created"] == 1

    return result["proposals"][0]["proposal_id"]


def test_submit_and_approve_proposal(proposal_scenario):

    proposal_id = create_draft_proposal(proposal_scenario)

    submit_result = submit_proposal(
        proposal_id=proposal_id,
        submitted_by="Test Submitter",
        remarks="Submitting for HR review."
    )

    assert submit_result["success"] is True
    assert submit_result["status"] == "SUBMITTED"

    approval_result = approve_proposal(
        proposal_id=proposal_id,
        approved_by="Test HR Manager",
        remarks="Compensation adjustment approved."
    )

    assert approval_result["success"] is True
    assert approval_result["status"] == "APPROVED"

    proposal = db.session.get(
        AdjustmentProposal,
        proposal_id
    )

    assert proposal.status == "APPROVED"
    assert proposal.approved_by == "Test HR Manager"
    assert proposal.approved_at is not None


def test_submit_and_reject_proposal(proposal_scenario):

    proposal_id = create_draft_proposal(proposal_scenario)

    submit_proposal(
        proposal_id=proposal_id,
        submitted_by="Test Submitter",
        remarks="Submitting for HR review."
    )

    result = reject_proposal(
        proposal_id=proposal_id,
        rejected_by="Test HR Manager",
        remarks="Further review is required."
    )

    assert result["success"] is True
    assert result["status"] == "REJECTED"

    proposal = db.session.get(
        AdjustmentProposal,
        proposal_id
    )

    assert proposal.status == "REJECTED"
    assert proposal.rejected_by == "Test HR Manager"
    assert proposal.rejected_at is not None


def test_cannot_approve_draft_proposal(proposal_scenario):

    proposal_id = create_draft_proposal(proposal_scenario)

    with pytest.raises(ValueError, match="Only SUBMITTED"):
        approve_proposal(
            proposal_id=proposal_id,
            approved_by="Test HR Manager",
            remarks="Attempting direct approval."
        )

    proposal = db.session.get(
        AdjustmentProposal,
        proposal_id
    )

    assert proposal.status == "DRAFT"


def test_cannot_reject_draft_proposal(proposal_scenario):

    proposal_id = create_draft_proposal(proposal_scenario)

    with pytest.raises(ValueError, match="Only SUBMITTED"):
        reject_proposal(
            proposal_id=proposal_id,
            rejected_by="Test HR Manager",
            remarks="Attempting direct rejection."
        )

    proposal = db.session.get(
        AdjustmentProposal,
        proposal_id
    )

    assert proposal.status == "DRAFT"


def test_submission_requires_remarks(proposal_scenario):

    proposal_id = create_draft_proposal(proposal_scenario)

    with pytest.raises(ValueError, match="Submission remarks"):
        submit_proposal(
            proposal_id=proposal_id,
            submitted_by="Test Submitter",
            remarks=""
        )

    proposal = db.session.get(
        AdjustmentProposal,
        proposal_id
    )

    assert proposal.status == "DRAFT"


def test_approval_creates_audit_and_history(proposal_scenario):

    proposal_id = create_draft_proposal(proposal_scenario)

    submit_proposal(
        proposal_id=proposal_id,
        submitted_by="Test Submitter",
        remarks="Submitted for review."
    )

    approve_proposal(
        proposal_id=proposal_id,
        approved_by="Test HR Manager",
        remarks="Approved after review."
    )

    history = ProposalHistory.query.filter_by(
        proposal_id=proposal_id
    ).order_by(
        ProposalHistory.changed_at.asc()
    ).all()

    audit = AuditLog.query.filter_by(
        entity_id=proposal_id
    ).all()

    assert len(history) == 3
    assert history[0].new_status == "DRAFT"
    assert history[1].new_status == "SUBMITTED"
    assert history[2].new_status == "APPROVED"

    assert len(audit) == 3
