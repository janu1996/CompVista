from flask import Blueprint, jsonify, request
from datetime import date, datetime

from services.compensation_analysis import analyze_compensation


analysis_bp = Blueprint(
    "analysis",
    __name__,
    url_prefix="/api/analysis"
)


@analysis_bp.route("/summary", methods=["GET"])
def get_analysis_summary():

    try:
        date_value = request.args.get("date")

        analysis_date = None

        if date_value:
            try:
                analysis_date = date.fromisoformat(date_value)
            except ValueError:
                return jsonify({
                    "success": False,
                    "message": "Invalid date format. Use YYYY-MM-DD."
                }), 400

        analysis = analyze_compensation(analysis_date)

        summary = analysis["summary"]

        return jsonify({
            "success": True,
            "message": "Analysis summary fetched successfully",
            "data": summary
        }), 200

    except Exception as e:

        return jsonify({
            "success": False,
            "message": "Failed to fetch analysis summary",
            "error": str(e)
        }), 500