
from flask import Flask
from flask_cors import CORS
from extensions import db
import os
from pathlib import Path

from routes.analysis_routes import analysis_bp
from routes.proposal_routes import proposal_bp

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
    ProposalHistory
)

app = Flask(__name__)

# Project directories
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

# Default database: original project database
default_db_path = BASE_DIR / "compvista.db"

# Optional database path from environment variable
configured_db_path = os.getenv("COMPVISTA_DB_PATH")

if configured_db_path:
    db_path = Path(configured_db_path)

    if not db_path.is_absolute():
        db_path = PROJECT_ROOT / db_path
else:
    db_path = default_db_path

# Ensure database directory exists
db_path.parent.mkdir(parents=True, exist_ok=True)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"sqlite:///{db_path.as_posix()}"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
CORS(app)

# Register API routes
app.register_blueprint(analysis_bp)
app.register_blueprint(proposal_bp)


@app.route("/")
def home():
    return {
        "message": "Welcome to CompVista!",
        "status": "Backend is running successfully"
    }


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("CompVista database tables ready!")
        print("Database location:", db_path)

    app.run(debug=True)
