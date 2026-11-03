
from pathlib import Path
import os

from flask import Flask
from flask_cors import CORS

from extensions import db, jwt

from routes.analysis_routes import analysis_bp
from routes.proposal_routes import proposal_bp
from routes.auth_routes import auth_bp

# Register all database models
from models import (
    Employee,
    Role,
    Level,
    Location,
    CompensationBand,
    SalaryRecord,
    PerformanceEvidence,
    Tenure,
    Promotion,
    AdjustmentProposal,
    AuditLog,
    ProposalHistory,
    EmployeeLocationHistory,
    User,
    FXRate,
)


def create_app(test_config=None):

    app = Flask(__name__)

    # Project directories
    base_dir = Path(__file__).resolve().parent
    project_root = base_dir.parent

    # Database configuration
    configured_db_path = os.getenv("COMPVISTA_DB_PATH")

    if configured_db_path:
        db_path = Path(configured_db_path)

        if not db_path.is_absolute():
            db_path = project_root / db_path
    else:
        db_path = base_dir / "compvista.db"

    db_path.parent.mkdir(parents=True, exist_ok=True)

    app.config.update(
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{db_path.as_posix()}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JSON_SORT_KEYS=False,

        # JWT configuration
        JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY"),
        JWT_ACCESS_TOKEN_EXPIRES=1800,
    )

    if test_config:
        app.config.update(test_config)

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)

    CORS(app)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(proposal_bp)

    @app.route("/")
    def home():
        return {
            "message": "Welcome to CompVista!",
            "status": "Backend is running successfully",
        }, 200

    @app.route("/health", methods=["GET"])
    def health():
        return {
            "success": True,
            "status": "healthy",
            "service": "CompVista API",
        }, 200

    return app


app = create_app()


if __name__ == "__main__":

    with app.app_context():
        db.create_all()

        print("CompVista database tables ready!")
        print(
            "Database location:",
            app.config["SQLALCHEMY_DATABASE_URI"]
        )

    debug_enabled = os.getenv(
        "FLASK_DEBUG", ""
    ).strip().lower() in {
        "1", "true", "yes", "on"
    }

    app.run(debug=debug_enabled)
