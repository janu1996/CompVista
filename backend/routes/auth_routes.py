
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
from models.employee import Employee


auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def get_current_user():
    """Return the authenticated active user."""
    identity = get_jwt_identity()

    try:
        user_id = int(identity)
    except (TypeError, ValueError):
        return None

    user = db.session.get(User, user_id)

    if not user or not user.is_active:
        return None

    return user


def staff_required(user):
    """Only HR and Admin can perform staff operations."""
    return user is not None and user.role in {"HR", "ADMIN"}


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

    user = get_current_user()

    if not user:
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


# -----------------------------------------
# 4. LINK CANDIDATE TO EMPLOYEE
# POST /api/auth/link-employee
# HR / ADMIN ONLY
# -----------------------------------------
@auth_bp.route("/link-employee", methods=["POST"])
@jwt_required()
def link_employee():

    staff_user = get_current_user()

    if not staff_required(staff_user):
        return jsonify({
            "success": False,
            "message": "Access denied. HR or Admin permission required."
        }), 403

    data = request.get_json(silent=True) or {}

    candidate_email = str(
        data.get("candidate_email", "")
    ).strip().lower()

    if not candidate_email:
        return jsonify({
            "success": False,
            "message": "Candidate email is required."
        }), 400

    try:
        valid_email = validate_email(
            candidate_email,
            check_deliverability=False
        )
        candidate_email = valid_email.normalized.lower()

    except EmailNotValidError:
        return jsonify({
            "success": False,
            "message": "Please enter a valid candidate email."
        }), 400

    # Find the registered candidate account.
    candidate = User.query.filter_by(
        email=candidate_email,
        role="CANDIDATE"
    ).with_for_update().first()

    if not candidate:
        return jsonify({
            "success": False,
            "message": "Candidate account not found."
        }), 404

    if not candidate.is_active:
        return jsonify({
            "success": False,
            "message": "Candidate account is inactive."
        }), 403

    if candidate.employee_id:
        return jsonify({
            "success": False,
            "message": "Candidate is already linked to an employee."
        }), 409

    # Employee is identified using the matching email.
    # The request never accepts an employee_id.
    employee = Employee.query.filter(
        db.func.lower(Employee.email) == candidate_email
    ).first()

    if not employee:
        return jsonify({
            "success": False,
            "message": "No matching employee record found for this email."
        }), 404

    # Prevent linking an employee already assigned to another account.
    existing_link = User.query.filter(
        User.employee_id == employee.employee_id
    ).first()

    if existing_link:
        return jsonify({
            "success": False,
            "message": "This employee is already linked to another account."
        }), 409

    try:
        candidate.employee_id = employee.employee_id

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Candidate successfully linked to employee record.",
            "data": {
                "user_id": candidate.user_id,
                "email": candidate.email,
                "employee_id": candidate.employee_id,
                "linked_by": staff_user.email
            }
        }), 200

    except IntegrityError:
        db.session.rollback()

        return jsonify({
            "success": False,
            "message": "Employee linking conflict. Please verify the account."
        }), 409

    except Exception:
        db.session.rollback()

        return jsonify({
            "success": False,
            "message": "Employee linking failed. Please try again."
        }), 500
