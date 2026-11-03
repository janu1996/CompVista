
from getpass import getpass

from app import create_app
from extensions import db
from models import User


def create_staff_user():
    app = create_app()

    with app.app_context():
        email = input("Enter staff email: ").strip().lower()

        if User.query.filter_by(email=email).first():
            print("An account with this email already exists.")
            return

        role = input("Enter role (HR/ADMIN): ").strip().upper()

        if role not in {"HR", "ADMIN"}:
            print("Invalid role. Only HR or ADMIN is allowed.")
            return

        password = getpass("Enter password (minimum 8 characters): ")

        if len(password) < 8:
            print("Password must contain at least 8 characters.")
            return

        confirm_password = getpass("Confirm password: ")

        if password != confirm_password:
            print("Passwords do not match.")
            return

        user = User(
            email=email,
            role=role,
            employee_id=None,
            is_active=True,
        )

        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        print("\nStaff account created successfully!")
        print("Email:", user.email)
        print("Role:", user.role)


if __name__ == "__main__":
    create_staff_user()
