
"""
CompVista - Role Master Data
Creates 40 unique roles while preserving existing records.
Uses the separate upgrade testing database.
"""

import os
import sys

# Always use the testing database for this script.
os.environ["COMPVISTA_DB_PATH"] = (
    "backend/compvista_upgrade_test.db"
)

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

BACKEND_PATH = os.path.join(PROJECT_ROOT, "backend")

if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

from app import app
from extensions import db
from models import Role


# 40 roles: existing 20 + additional 20
ROLE_DATA = [
    # Existing roles
    ("Software Engineer", "Engineering", "Technology"),
    ("Frontend Developer", "Engineering", "Technology"),
    ("Backend Developer", "Engineering", "Technology"),
    ("Full Stack Developer", "Engineering", "Technology"),
    ("Data Analyst", "Analytics", "Data"),
    ("Data Scientist", "Analytics", "Data"),
    ("ML Engineer", "AI", "Data"),
    ("DevOps Engineer", "Engineering", "Technology"),
    ("QA Engineer", "Quality", "Technology"),
    ("Product Manager", "Product", "Management"),
    ("UI UX Designer", "Design", "Creative"),
    ("HR Executive", "Human Resources", "Corporate"),
    ("HR Manager", "Human Resources", "Management"),
    ("Finance Analyst", "Finance", "Corporate"),
    ("Business Analyst", "Business", "Corporate"),
    ("Project Manager", "Delivery", "Management"),
    ("Cybersecurity Analyst", "Security", "Technology"),
    ("Cloud Architect", "Engineering", "Technology"),
    ("Technical Writer", "Documentation", "Corporate"),
    ("Customer Success Manager", "Support", "Management"),

    # Additional 20 roles
    ("Data Engineer", "Analytics", "Data"),
    ("Database Administrator", "Engineering", "Technology"),
    ("Mobile App Developer", "Engineering", "Technology"),
    ("Python Developer", "Engineering", "Technology"),
    ("Java Developer", "Engineering", "Technology"),
    ("Automation Test Engineer", "Quality", "Technology"),
    ("Security Engineer", "Security", "Technology"),
    ("Network Engineer", "Infrastructure", "Technology"),
    ("System Administrator", "IT Operations", "Technology"),
    ("Site Reliability Engineer", "Engineering", "Technology"),
    ("AI Research Scientist", "AI", "Data"),
    ("Business Intelligence Developer", "Analytics", "Data"),
    ("UX Researcher", "Design", "Creative"),
    ("Graphic Designer", "Design", "Creative"),
    ("Talent Acquisition Specialist", "Human Resources", "Corporate"),
    ("Payroll Specialist", "Finance", "Corporate"),
    ("Accountant", "Finance", "Corporate"),
    ("Marketing Manager", "Marketing", "Management"),
    ("Operations Manager", "Operations", "Management"),
    ("Technical Support Engineer", "Support", "Technology"),
]


def create_roles():

    with app.app_context():

        # Safety check: never modify the original database.
        database_uri = app.config["SQLALCHEMY_DATABASE_URI"]

        if "compvista_upgrade_test.db" not in database_uri:
            raise RuntimeError(
                "Safety check failed: testing database not selected."
            )

        existing_roles = {
            role.role_name: role
            for role in Role.query.all()
        }

        added = 0
        skipped = 0

        for role_name, department, job_family in ROLE_DATA:

            if role_name in existing_roles:
                skipped += 1
                continue

            new_role = Role(
                role_name=role_name,
                department=department,
                job_family=job_family,
                description=f"{role_name} position"
            )

            db.session.add(new_role)
            added += 1

        try:
            db.session.commit()

        except Exception:
            db.session.rollback()
            raise

        total_roles = Role.query.count()

        print("\nCOMPVISTA ROLE MASTER DATA")
        print("==========================")
        print("Roles added:", added)
        print("Existing roles skipped:", skipped)
        print("Total roles:", total_roles)
        print("Expected roles:", 40)

        if total_roles != 40:
            raise RuntimeError(
                f"Expected 40 roles, but found {total_roles}."
            )

        print("\nRole master data created successfully!")


if __name__ == "__main__":
    create_roles()
