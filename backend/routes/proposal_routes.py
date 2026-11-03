
from datetime import date

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models import AdjustmentProposal, ProposalHistory, User

from services.proposal_service import generate_adjustment_proposals

from services.approval_service import (
    get_proposal,
    submit_proposal,
    approve_proposal,
    reject_proposal,
    apply_proposal,
)


proposal_bp = Blueprint(
    "proposals",
    __name__,
    url_prefix="/api/proposals",
)

VALID_STATUSES = {
    "DRAFT",
    "SUBMITTED",
    "APPROVED",
    "REJECTED",
    "APPLIED",
}

ALLOWED_STAFF_ROLES = {"HR", "ADMIN"}

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


# --------------------------------------------------
# AUTHENTICATION HELPERS
# --------------------------------------------------

def _error(message, status_code):
    return jsonify({
        "success": False,
        "message": message,
    }), status_code


def _current_user():
    identity = get_jwt_identity()

    try:
        user_id = int(identity)
    except (TypeError, ValueError):
        return None

    user = db.session.get(User, user_id)

    if not user or not user.is_active:
        return None

    return user


def _staff_required(user):
    if user.role not in ALLOWED_STAFF_ROLES:
        return _error(
            "You do not have permission to perform this action.",
            403,
        )

    return None


# --------------------------------------------------
# SERIALIZATION
# --------------------------------------------------

def serialize_proposal(proposal):
    return {
        "proposal_id": proposal.proposal_id,
        "employee_id": proposal.employee_id,
        "current_salary_id": proposal.current_salary_id,
        "proposed_salary": str(proposal.proposed_salary),
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
        ),
    }


def _json_body():
    data = request.get_json(silent=True)

    if data is None:
        return {}

    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object.")

    return data


# --------------------------------------------------
# 1. GET ALL PROPOSALS
# GET /api/proposals/
# Candidate: own employee proposals only
# HR/Admin: all proposals
# --------------------------------------------------

@proposal_bp.route("/", methods=["GET"])
@jwt_required()
def get_all_proposals():

    try:
        user = _current_user()

        if not user:
            return _error("User account not found or inactive.", 401)

        page_raw = request.args.get("page", "1")
        per_page_raw = request.args.get(
            "per_page",
            str(DEFAULT_PAGE_SIZE),
        )

        try:
            page = int(page_raw)
            per_page = int(per_page_raw)
        except (TypeError, ValueError):
            return _error(
                "page and per_page must be integers.",
                400,
            )

        if page < 1:
            return _error(
                "page must be greater than or equal to 1.",
                400,
            )

        if per_page < 1 or per_page > MAX_PAGE_SIZE:
            return _error(
                f"per_page must be between 1 and {MAX_PAGE_SIZE}.",
                400,
            )

        query = AdjustmentProposal.query

        # Candidates can only access their linked employee records.
        if user.role == "CANDIDATE":
            if not user.employee_id:
                return jsonify({
                    "success": True,
                    "total": 0,
                    "page": page,
                    "per_page": per_page,
                    "pages": 0,
                    "data": [],
                }), 200

            query = query.filter(
                AdjustmentProposal.employee_id == user.employee_id
            )

        elif user.role not in ALLOWED_STAFF_ROLES:
            return _error("Unauthorized role.", 403)

        # Optional filters
        status = request.args.get("status")

        if status:
            status = status.strip().upper()

            if status not in VALID_STATUSES:
                return _error(
                    "Invalid proposal status filter.",
                    400,
                )

            query = query.filter(
                AdjustmentProposal.status == status
            )

        employee_id = request.args.get("employee_id")

        # Staff may filter by employee ID.
        # Candidate ownership filter is never overridden.
        if employee_id and user.role in ALLOWED_STAFF_ROLES:
            query = query.filter(
                AdjustmentProposal.employee_id == employee_id.strip()
            )

        total = query.count()

        proposals = (
            query.order_by(
                AdjustmentProposal.created_at.desc()
            )
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return jsonify({
            "success": True,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page,
            "data": [
                serialize_proposal(item)
                for item in proposals
            ],
        }), 200

    except Exception:
        return _error("Failed to fetch proposals.", 500)


# --------------------------------------------------
# 2. GET PROPOSAL DETAILS
# GET /api/proposals/<proposal_id>
# --------------------------------------------------

@proposal_bp.route(
    "/<string:proposal_id>",
    methods=["GET"],
)
@jwt_required()
def get_proposal_details(proposal_id):

    try:
        user = _current_user()

        if not user:
            return _error("User account not found or inactive.", 401)

        proposal = get_proposal(proposal_id)

        # Candidate ownership validation
        if user.role == "CANDIDATE":
            if (
                not user.employee_id
                or proposal.employee_id != user.employee_id
            ):
                return _error("Proposal not found.", 404)

        elif user.role not in ALLOWED_STAFF_ROLES:
            return _error("Unauthorized role.", 403)

        history = ProposalHistory.query.filter_by(
            proposal_id=proposal_id
        ).order_by(
            ProposalHistory.changed_at.asc()
        ).all()

        data = serialize_proposal(proposal)

        data["history"] = [
            {
                "previous_status": item.previous_status,
                "new_status": item.new_status,
                "changed_by": item.changed_by,
                "remarks": item.remarks,
                "changed_at": (
                    item.changed_at.isoformat()
                    if item.changed_at else None
                ),
            }
            for item in history
        ]

        return jsonify({
            "success": True,
            "data": data,
        }), 200

    except ValueError as exc:
        return _error(str(exc), 404)

    except Exception:
        return _error("Failed to fetch proposal details.", 500)


# --------------------------------------------------
# 3. GENERATE PROPOSALS
# POST /api/proposals/generate
# HR/Admin only
# --------------------------------------------------

@proposal_bp.route("/generate", methods=["POST"])
@jwt_required()
def generate_proposals():

    try:
        user = _current_user()

        if not user:
            return _error("User account not found or inactive.", 401)

        permission_error = _staff_required(user)

        if permission_error:
            return permission_error

        data = _json_body()
        date_value = data.get("date")

        if date_value in (None, ""):
            analysis_date = None
        else:
            if not isinstance(date_value, str):
                return _error(
                    "Invalid date. Use YYYY-MM-DD.",
                    400,
                )

            try:
                analysis_date = date.fromisoformat(date_value)
            except ValueError:
                return _error(
                    "Invalid date. Use YYYY-MM-DD.",
                    400,
                )

        # Actor comes from authenticated account,
        # never from the request body.
        result = generate_adjustment_proposals(
            as_of_date=analysis_date,
            proposed_by=user.email,
        )

        return jsonify({
            "success": True,
            "message": result["message"],
            "data": result,
        }), 201

    except ValueError as exc:
        return _error(str(exc), 400)

    except Exception:
        return _error("Proposal generation failed.", 500)


# --------------------------------------------------
# COMMON PROPOSAL ACTION
# --------------------------------------------------

def _run_proposal_action(
    action,
    proposal_id,
    actor,
    actor_label,
):

    try:
        data = _json_body()
        remarks = data.get("remarks")

        if remarks is not None and not isinstance(remarks, str):
            return _error("Remarks must be text.", 400)

        result = action(
            proposal_id,
            actor.email,
            remarks,
        )

        return jsonify({
            "success": True,
            "message": result["message"],
            "data": result,
        }), 200

    except ValueError as exc:
        return _error(str(exc), 400)

    except Exception:
        return _error(
            f"{actor_label} failed.",
            500,
        )


# --------------------------------------------------
# 4. SUBMIT PROPOSAL
# HR/Admin only
# --------------------------------------------------

@proposal_bp.route(
    "/<string:proposal_id>/submit",
    methods=["POST"],
)
@jwt_required()
def submit_proposal_api(proposal_id):

    user = _current_user()

    if not user:
        return _error("User account not found or inactive.", 401)

    permission_error = _staff_required(user)

    if permission_error:
        return permission_error

    return _run_proposal_action(
        submit_proposal,
        proposal_id,
        user,
        "Proposal submission",
    )


# --------------------------------------------------
# 5. APPROVE PROPOSAL
# HR/Admin only
# --------------------------------------------------

@proposal_bp.route(
    "/<string:proposal_id>/approve",
    methods=["POST"],
)
@jwt_required()
def approve_proposal_api(proposal_id):

    user = _current_user()

    if not user:
        return _error("User account not found or inactive.", 401)

    permission_error = _staff_required(user)

    if permission_error:
        return permission_error

    return _run_proposal_action(
        approve_proposal,
        proposal_id,
        user,
        "Proposal approval",
    )


# --------------------------------------------------
# 6. REJECT PROPOSAL
# HR/Admin only
# --------------------------------------------------

@proposal_bp.route(
    "/<string:proposal_id>/reject",
    methods=["POST"],
)
@jwt_required()
def reject_proposal_api(proposal_id):

    user = _current_user()

    if not user:
        return _error("User account not found or inactive.", 401)

    permission_error = _staff_required(user)

    if permission_error:
        return permission_error

    return _run_proposal_action(
        reject_proposal,
        proposal_id,
        user,
        "Proposal rejection",
    )


# --------------------------------------------------
# 7. APPLY APPROVED PROPOSAL
# HR/Admin only
# --------------------------------------------------

@proposal_bp.route(
    "/<string:proposal_id>/apply",
    methods=["POST"],
)
@jwt_required()
def apply_proposal_api(proposal_id):

    try:
        user = _current_user()

        if not user:
            return _error("User account not found or inactive.", 401)

        permission_error = _staff_required(user)

        if permission_error:
            return permission_error

        result = apply_proposal(
            proposal_id,
            user.email,
        )

        return jsonify({
            "success": True,
            "message": result["message"],
            "data": result,
        }), 200

    except ValueError as exc:
        return _error(str(exc), 400)

    except Exception:
        return _error("Salary adjustment failed.", 500)
