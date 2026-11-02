
from flask import Blueprint, jsonify, request
from datetime import date

from models import AdjustmentProposal, ProposalHistory
from services.proposal_service import generate_adjustment_proposals
from services.approval_service import (
    get_proposal,
    submit_proposal,
    approve_proposal,
    reject_proposal,
    apply_proposal
)


proposal_bp = Blueprint(
    "proposals",
    __name__,
    url_prefix="/api/proposals"
)


# --------------------------------------------------
# HELPER: CONVERT PROPOSAL TO JSON
# --------------------------------------------------

def serialize_proposal(proposal):

    return {
        "proposal_id": proposal.proposal_id,
        "employee_id": proposal.employee_id,
        "current_salary_id": proposal.current_salary_id,
        "proposed_salary": float(proposal.proposed_salary),
        "currency_code": proposal.currency_code,
        "reason": proposal.reason,
        "issue_type": proposal.issue_type,
        "status": proposal.status,
        "proposed_by": proposal.proposed_by,

        "approved_by": proposal.approved_by,
        "approved_at": (
            proposal.approved_at.isoformat()
            if proposal.approved_at else None
        ),

        "rejected_by": proposal.rejected_by,
        "rejected_at": (
            proposal.rejected_at.isoformat()
            if proposal.rejected_at else None
        ),

        "created_at": (
            proposal.created_at.isoformat()
            if proposal.created_at else None
        ),

        "applied_at": (
            proposal.applied_at.isoformat()
            if proposal.applied_at else None
        )
    }


# --------------------------------------------------
# 1. GET ALL PROPOSALS
# GET /api/proposals/
# --------------------------------------------------

@proposal_bp.route("/", methods=["GET"])
def get_all_proposals():

    try:
        proposals = AdjustmentProposal.query.order_by(
            AdjustmentProposal.created_at.desc()
        ).all()

        return jsonify({
            "success": True,
            "total": len(proposals),
            "data": [
                serialize_proposal(proposal)
                for proposal in proposals
            ]
        }), 200

    except Exception as e:

        return jsonify({
            "success": False,
            "message": "Failed to fetch proposals",
            "error": str(e)
        }), 500


# --------------------------------------------------
# 2. GET PROPOSAL DETAILS
# GET /api/proposals/<proposal_id>
# --------------------------------------------------

@proposal_bp.route(
    "/<string:proposal_id>",
    methods=["GET"]
)
def get_proposal_details(proposal_id):

    try:
        proposal = get_proposal(proposal_id)

        history = ProposalHistory.query.filter_by(
            proposal_id=proposal_id
        ).order_by(
            ProposalHistory.changed_at.asc()
        ).all()

        history_data = []

        for item in history:

            history_data.append({
                "previous_status": item.previous_status,
                "new_status": item.new_status,
                "changed_by": item.changed_by,
                "remarks": item.remarks,
                "changed_at": (
                    item.changed_at.isoformat()
                    if item.changed_at else None
                )
            })

        data = serialize_proposal(proposal)
        data["history"] = history_data

        return jsonify({
            "success": True,
            "data": data
        }), 200

    except ValueError as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 404

    except Exception as e:

        return jsonify({
            "success": False,
            "message": "Failed to fetch proposal details",
            "error": str(e)
        }), 500


# --------------------------------------------------
# 3. GENERATE PROPOSALS
# POST /api/proposals/generate
# --------------------------------------------------

@proposal_bp.route(
    "/generate",
    methods=["POST"]
)
def generate_proposals():

    try:
        data = request.get_json(silent=True) or {}

        date_value = data.get("date")

        proposed_by = data.get(
            "proposed_by",
            "CompVista Analysis Engine"
        )

        analysis_date = None

        if date_value:
            try:
                analysis_date = date.fromisoformat(date_value)

            except (ValueError, TypeError):
                return jsonify({
                    "success": False,
                    "message": "Invalid date. Use YYYY-MM-DD."
                }), 400

        if (
            not isinstance(proposed_by, str)
            or not proposed_by.strip()
        ):
            return jsonify({
                "success": False,
                "message": "Proposed by name is required."
            }), 400

        result = generate_adjustment_proposals(
            as_of_date=analysis_date,
            proposed_by=proposed_by.strip()
        )

        return jsonify({
            "success": True,
            "message": result["message"],
            "data": result
        }), 201

    except Exception as e:

        return jsonify({
            "success": False,
            "message": "Proposal generation failed",
            "error": str(e)
        }), 500


# --------------------------------------------------
# 4. SUBMIT PROPOSAL
# POST /api/proposals/<proposal_id>/submit
# --------------------------------------------------

@proposal_bp.route(
    "/<string:proposal_id>/submit",
    methods=["POST"]
)
def submit_proposal_api(proposal_id):

    try:
        data = request.get_json(silent=True) or {}

        submitted_by = data.get("submitted_by")
        remarks = data.get("remarks")

        result = submit_proposal(
            proposal_id,
            submitted_by,
            remarks
        )

        return jsonify({
            "success": True,
            "message": result["message"],
            "data": result
        }), 200

    except ValueError as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 400

    except Exception as e:

        return jsonify({
            "success": False,
            "message": "Proposal submission failed",
            "error": str(e)
        }), 500


# --------------------------------------------------
# 5. APPROVE PROPOSAL
# POST /api/proposals/<proposal_id>/approve
# --------------------------------------------------

@proposal_bp.route(
    "/<string:proposal_id>/approve",
    methods=["POST"]
)
def approve_proposal_api(proposal_id):

    try:
        data = request.get_json(silent=True) or {}

        approved_by = data.get("approved_by")
        remarks = data.get("remarks")

        result = approve_proposal(
            proposal_id,
            approved_by,
            remarks
        )

        return jsonify({
            "success": True,
            "message": result["message"],
            "data": result
        }), 200

    except ValueError as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 400

    except Exception as e:

        return jsonify({
            "success": False,
            "message": "Proposal approval failed",
            "error": str(e)
        }), 500


# --------------------------------------------------
# 6. REJECT PROPOSAL
# POST /api/proposals/<proposal_id>/reject
# --------------------------------------------------

@proposal_bp.route(
    "/<string:proposal_id>/reject",
    methods=["POST"]
)
def reject_proposal_api(proposal_id):

    try:
        data = request.get_json(silent=True) or {}

        rejected_by = data.get("rejected_by")
        remarks = data.get("remarks")

        result = reject_proposal(
            proposal_id,
            rejected_by,
            remarks
        )

        return jsonify({
            "success": True,
            "message": result["message"],
            "data": result
        }), 200

    except ValueError as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 400

    except Exception as e:

        return jsonify({
            "success": False,
            "message": "Proposal rejection failed",
            "error": str(e)
        }), 500


# --------------------------------------------------
# 7. APPLY APPROVED PROPOSAL
# POST /api/proposals/<proposal_id>/apply
# --------------------------------------------------

@proposal_bp.route(
    "/<string:proposal_id>/apply",
    methods=["POST"]
)
def apply_proposal_api(proposal_id):

    try:
        data = request.get_json(silent=True) or {}

        applied_by = data.get("applied_by")

        result = apply_proposal(
            proposal_id,
            applied_by
        )

        return jsonify({
            "success": True,
            "message": result["message"],
            "data": result
        }), 200

    except ValueError as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 400

    except Exception as e:

        return jsonify({
            "success": False,
            "message": "Salary adjustment failed",
            "error": str(e)
        }), 500
