
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
from email_validator import validate_email, EmailNotValidError
from sqlalchemy.exc import IntegrityError

from extensions import db
from models.user import User


auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


# -----------------------------------------
# 1. REGISTER CANDIDATE
# POST /api/auth/register
# -----------------------------------------
@auth_bp.route("/register", methods=["POST"])
def register():

    data = request.get_json(silent=True) or {}

    email = str(data.get("email", "")).strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({
            "success": False,
            "message": "Email and password are required."
        }), 400

    try:
        valid_email = validate_email(
            email,
            check_deliverability=False
        )
        email = valid_email.normalized.lower()

    except EmailNotValidError:
        return jsonify({
            "success": False,
            "message": "Please enter a valid email address."
        }), 400

    if not isinstance(password, str) or len(password) < 8:
        return jsonify({
            "success": False,
            "message": "Password must contain at least 8 characters."
        }), 400

    if User.query.filter_by(email=email).first():
        return jsonify({
            "success": False,
            "message": "An account with this email already exists."
        }), 409

    try:
        user = User(
            email=email,
            role="CANDIDATE",
            employee_id=None,
            is_active=True
        )

        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Candidate account created successfully.",
            "data": {
                "user_id": user.user_id,
                "email": user.email,
                "role": user.role
            }
        }), 201

    except IntegrityError:
        db.session.rollback()

        return jsonify({
            "success": False,
            "message": "An account with this email already exists."
        }), 409

    except Exception:
        db.session.rollback()

        return jsonify({
            "success": False,
            "message": "Registration failed. Please try again."
        }), 500


# -----------------------------------------
# 2. LOGIN
# POST /api/auth/login
# -----------------------------------------
@auth_bp.route("/login", methods=["POST"])
def login():

    data = request.get_json(silent=True) or {}

    email = str(data.get("email", "")).strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({
            "success": False,
            "message": "Email and password are required."
        }), 400

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({
            "success": False,
            "message": "Invalid email or password."
        }), 401

    if not user.is_active:
        return jsonify({
            "success": False,
            "message": "This account is inactive."
        }), 403

    access_token = create_access_token(
        identity=str(user.user_id),
        additional_claims={
            "role": user.role
        }
    )

    return jsonify({
        "success": True,
        "message": "Login successful.",
        "data": {
            "access_token": access_token,
            "token_type": "Bearer",
            "user": {
                "user_id": user.user_id,
                "email": user.email,
                "role": user.role
            }
        }
    }), 200


# -----------------------------------------
# 3. CURRENT USER PROFILE
# GET /api/auth/me
# -----------------------------------------
@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def current_user():

    identity = get_jwt_identity()

    try:
        user_id = int(identity)
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "Invalid authentication token."
        }), 401

    user = db.session.get(User, user_id)

    if not user or not user.is_active:
        return jsonify({
            "success": False,
            "message": "User account not found or inactive."
        }), 401

    return jsonify({
        "success": True,
        "data": {
            "user_id": user.user_id,
            "email": user.email,
            "role": user.role,
            "employee_id": user.employee_id
        }
    }), 200
