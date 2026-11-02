
from flask import Flask
from extensions import db
import os

app = Flask(__name__)

# Database configuration
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///" + os.path.join(BASE_DIR, "compvista.db")
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database
db.init_app(app)


@app.route("/")
def home():
    return {
        "message": "Welcome to CompVista!",
        "status": "Backend is running successfully"
    }


if __name__ == "__main__":
    app.run(debug=True)
