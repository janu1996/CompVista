
from datetime import date, datetime
from decimal import Decimal

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models import User
from services.compensation_analysis import analyze_compensation


analysis_bp = Blueprint(
    "analysis",
    __name__,
    url_prefix="/api/analysis",
)


def _json_safe(value):
    """Convert analysis values into JSON-safe, precision-safe values."""
    if isinstance(value, Decimal):
        return str(value)

    if isinstance(value, (date, datetime)):
        return value.isoformat()

    if isinstance(value, dict):
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]

    return value


def _parse_analysis_date(raw_value):
    if raw_value in (None, ""):
        return None

    try:
        return date.fromisoformat(raw_value)
    except (TypeError, ValueError):
        raise ValueError("Invalid date format. Use YYYY-MM-DD.")


def _current_user():
    user_id = get_jwt_identity()
    return db.session.get(User, int(user_id))


def _staff_required(user):
    return user is not None and user.is_active and user.role in {
        "HR",
        "ADMIN",
    }


@analysis_bp.route("/summary", methods=["GET"])
@jwt_required()
def get_analysis_summary():
    user = _current_user()

    if not _staff_required(user):
        return jsonify({
            "success": False,
            "message": "Access denied. HR or Admin permission required.",
        }), 403

    try:
        analysis_date = _parse_analysis_date(
            request.args.get("date")
        )

        analysis = analyze_compensation(analysis_date)

        return jsonify({
            "success": True,
            "message": "Analysis summary fetched successfully.",
            "data": _json_safe(analysis["summary"]),
        }), 200

    except ValueError as exc:
        return jsonify({
            "success": False,
            "message": str(exc),
        }), 400

    except Exception:
        return jsonify({
            "success": False,
            "message": "Failed to fetch analysis summary.",
        }), 500


@analysis_bp.route("/results", methods=["GET"])
@jwt_required()
def get_analysis_results():
    """Return complete employee-level analysis to HR and Admin."""
    user = _current_user()

    if not _staff_required(user):
        return jsonify({
            "success": False,
            "message": "Access denied. HR or Admin permission required.",
        }), 403

    try:
        analysis_date = _parse_analysis_date(
            request.args.get("date")
        )

        analysis = analyze_compensation(analysis_date)

        return jsonify({
            "success": True,
            "message": "Analysis results fetched successfully.",
            "data": {
                "summary": _json_safe(analysis["summary"]),
                "results": _json_safe(analysis["results"]),
            },
        }), 200

    except ValueError as exc:
        return jsonify({
            "success": False,
            "message": str(exc),
        }), 400

    except Exception:
        return jsonify({
            "success": False,
            "message": "Failed to fetch analysis results.",
        }), 500


@analysis_bp.route("/me", methods=["GET"])
@jwt_required()
def get_my_analysis():
    """Allow a linked candidate to view only their own analysis."""
    user = _current_user()

    if user is None or not user.is_active:
        return jsonify({
            "success": False,
            "message": "User account not found or inactive.",
        }), 401

    if user.role != "CANDIDATE":
        return jsonify({
            "success": False,
            "message": "This endpoint is available only to candidates.",
        }), 403

    if not user.employee_id:
        return jsonify({
            "success": False,
            "message": (
                "Your account is not linked to an employee record. "
                "Please contact HR."
            ),
        }), 403

    try:
        analysis_date = _parse_analysis_date(
            request.args.get("date")
        )

        analysis = analyze_compensation(analysis_date)

        # Filter on the server using the authenticated user's employee ID.
        # Never accept an employee_id from the candidate's request.
        own_results = [
            result
            for result in analysis["results"]
            if str(result.get("employee_id")) == str(user.employee_id)
        ]

        if not own_results:
            return jsonify({
                "success": False,
                "message": "No compensation analysis found for your account.",
            }), 404

        return jsonify({
            "success": True,
            "message": "Your compensation analysis fetched successfully.",
            "data": {
                "results": _json_safe(own_results),
            },
        }), 200

    except ValueError as exc:
        return jsonify({
            "success": False,
            "message": str(exc),
        }), 400

    except Exception:
        return jsonify({
            "success": False,
            "message": "Failed to fetch your compensation analysis.",
        }), 500
