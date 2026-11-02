
import os
import sys

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

sys.path.insert(
    0,
    os.path.join(PROJECT_ROOT, "backend")
)

from app import app

from models import (
    AdjustmentProposal,
    AuditLog,
    ProposalHistory
)

from services.approval_service import (
    approve_proposal,
    reject_proposal
)


with app.app_context():

    print("\nCOMPVISTA HR APPROVAL WORKFLOW")
    print("=" * 45)

    # Get two DRAFT proposals
    draft_proposals = AdjustmentProposal.query.filter_by(
        status="DRAFT"
    ).order_by(
        AdjustmentProposal.proposal_id
    ).limit(2).all()

    if len(draft_proposals) < 2:
        print("Two DRAFT proposals are not available.")
    else:

        # --------------------------------------
        # 1. APPROVE FIRST PROPOSAL
        # --------------------------------------

        first_proposal = draft_proposals[0]

        print("\nAPPROVING PROPOSAL")
        print("-" * 45)

        result = approve_proposal(
            proposal_id=first_proposal.proposal_id,
            approved_by="HR Manager",
            remarks="Reviewed compensation evidence and approved."
        )

        print(result)

        # --------------------------------------
        # 2. REJECT SECOND PROPOSAL
        # --------------------------------------

        second_proposal = draft_proposals[1]

        print("\nREJECTING PROPOSAL")
        print("-" * 45)

        result = reject_proposal(
            proposal_id=second_proposal.proposal_id,
            rejected_by="HR Manager",
            remarks="Further compensation review is required."
        )

        print(result)

        # --------------------------------------
        # 3. VERIFY DATABASE
        # --------------------------------------

        print("\nDATABASE VERIFICATION")
        print("-" * 45)

        print(
            "Total Proposals:",
            AdjustmentProposal.query.count()
        )

        print(
            "Approved:",
            AdjustmentProposal.query.filter_by(
                status="APPROVED"
            ).count()
        )

        print(
            "Rejected:",
            AdjustmentProposal.query.filter_by(
                status="REJECTED"
            ).count()
        )

        print(
            "Draft:",
            AdjustmentProposal.query.filter_by(
                status="DRAFT"
            ).count()
        )

        # --------------------------------------
        # 4. VERIFY HISTORY AND AUDIT
        # --------------------------------------

        for proposal in [first_proposal, second_proposal]:

            print("\nProposal:", proposal.proposal_id)
            print("Status:", proposal.status)

            print(
                "History:",
                ProposalHistory.query.filter_by(
                    proposal_id=proposal.proposal_id
                ).count()
            )

            print(
                "Audit:",
                AuditLog.query.filter_by(
                    entity_id=proposal.proposal_id
                ).count()
            )

    print("\nApproval workflow testing completed!")
