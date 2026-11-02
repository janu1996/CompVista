
from extensions import db


class Role(db.Model):
    __tablename__ = "roles"

    role_id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    role_name = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    department = db.Column(db.String(100), nullable=False)

    job_family = db.Column(db.String(100), nullable=False)

    description = db.Column(db.Text)

    def __repr__(self):
        return f"<Role {self.role_name}>"
