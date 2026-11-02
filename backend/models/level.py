
from extensions import db


class Level(db.Model):
    __tablename__ = "levels"

    level_id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    level_name = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    level_rank = db.Column(
        db.Integer,
        unique=True,
        nullable=False
    )

    description = db.Column(db.Text)

    def __repr__(self):
        return f"<Level {self.level_name}>"
