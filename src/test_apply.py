
import os
import sys

# Project root path
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

# Add backend folder to Python path BEFORE imports
BACKEND_PATH = os.path.join(PROJECT_ROOT, "backend")

sys.path.insert(0, BACKEND_PATH)

# Now import backend modules
from app import app
from extensions import db

from models import (
    AdjustmentProposal,
    SalaryRecord,
    AuditLog,
    ProposalHistory
)

from services.approval_service import apply_proposal


with app.app_context():

    print("\nCOMPVISTA SALARY APPLICATION TEST")
    print("=" * 45)

    proposal_id = "PROP-P-000002--000002-2026"

    proposal = AdjustmentProposal.query.filter_by(
        proposal_id=proposal_id
    ).first()

    if not proposal:
        print("Proposal not found.")

    elif proposal.status != "APPROVED":
        print("Proposal must be APPROVED before applying.")

    else:

        old_salary_id = proposal.current_salary_id

        old_salary = SalaryRecord.query.filter_by(
            salary_id=old_salary_id
        ).first()

        print("\nBEFORE APPLICATION")
        print("Proposal Status:", proposal.status)
        print("Old Salary:", old_salary.base_salary)
        print("Old Effective To:", old_salary.effective_to)

        # Apply approved proposal
        result = apply_proposal(
            proposal_id=proposal_id,
            applied_by="HR Administrator"
        )

        print("\nAPPLICATION RESULT")
        print(result)

        # Refresh database objects
        db.session.refresh(proposal)
        db.session.refresh(old_salary)

        new_salary = SalaryRecord.query.filter_by(
            salary_id=result["new_salary_id"]
        ).first()

        print("\nAFTER APPLICATION")
        print("Proposal Status:", proposal.status)
        print("Old Salary Effective To:", old_salary.effective_to)

        if new_salary:
            print("New Salary ID:", new_salary.salary_id)
            print("New Salary:", new_salary.base_salary)
            print("New Salary Effective From:", new_salary.effective_from)

        print("\nAUDIT AND HISTORY")
        print(
            "Audit Entries:",
            AuditLog.query.filter_by(
                entity_id=proposal_id
            ).count()
        )

        print(
            "History Entries:",
            ProposalHistory.query.filter_by(
                proposal_id=proposal_id
            ).count()
        )

    print("\nSalary application test completed!")
