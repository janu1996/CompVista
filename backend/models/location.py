
from extensions import db


class Location(db.Model):
    __tablename__ = "locations"

    location_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    location_name = db.Column(db.String(100), nullable=False)

    country = db.Column(db.String(100), nullable=False)

    country_code = db.Column(db.String(5), nullable=False)

    currency_code = db.Column(db.String(5), nullable=False)

    cost_of_living_index = db.Column(
        db.Float,
        nullable=False,
        default=1.0
    )

    def __repr__(self):
        return f"<Location {self.location_name}>"
