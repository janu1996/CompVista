
import os
import sys

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

BACKEND_PATH = os.path.join(PROJECT_ROOT, "backend")

sys.path.insert(0, BACKEND_PATH)

from app import app

from services.proposal_service import generate_adjustment_proposals

from models import (
    AdjustmentProposal,
    AuditLog,
    ProposalHistory
)


with app.app_context():

    print("\nCOMPVISTA ADJUSTMENT PROPOSAL TEST")
    print("=" * 45)

    # Generate proposals
    result = generate_adjustment_proposals()

    print("\nGENERATION SUMMARY")
    print("-" * 45)

    print("Message:", result["message"])
    print("Analysis Date:", result["analysis_date"])
    print("Flagged Employees:", result["flagged_employees"])
    print("Proposals Created:", result["proposals_created"])
    print("Proposals Skipped:", result["proposals_skipped"])

    # Verify database records
    print("\nDATABASE VERIFICATION")
    print("-" * 45)

    print(
        "Total Proposals:",
        AdjustmentProposal.query.count()
    )

    print(
        "Total Audit Logs:",
        AuditLog.query.count()
    )

    print(
        "Total Proposal History:",
        ProposalHistory.query.count()
    )

    # Display sample proposals
    print("\nSAMPLE PROPOSALS")
    print("-" * 45)

    proposals = AdjustmentProposal.query.order_by(
        AdjustmentProposal.created_at.desc()
    ).limit(5).all()

    for proposal in proposals:

        print("\nProposal ID:", proposal.proposal_id)
        print("Employee ID:", proposal.employee_id)
        print("Current Salary ID:", proposal.current_salary_id)
        print("Proposed Salary:", proposal.proposed_salary)
        print("Currency:", proposal.currency_code)
        print("Issue Type:", proposal.issue_type)
        print("Status:", proposal.status)

    # Verify audit and history for sample
    if proposals:

        sample = proposals[0]

        print("\nRECORD LINK VERIFICATION")
        print("-" * 45)

        print(
            "Audit entries:",
            AuditLog.query.filter_by(
                entity_id=sample.proposal_id
            ).count()
        )

        print(
            "History entries:",
            ProposalHistory.query.filter_by(
                proposal_id=sample.proposal_id
            ).count()
        )

    print("\nProposal testing completed!")
