
from extensions import db


class CompensationBand(db.Model):
    __tablename__ = "compensation_bands"

    band_id = db.Column(db.String(100), primary_key=True)

    role_id = db.Column(
        db.Integer,
        db.ForeignKey("roles.role_id"),
        nullable=False
    )

    level_id = db.Column(
        db.Integer,
        db.ForeignKey("levels.level_id"),
        nullable=False
    )

    location_id = db.Column(
        db.Integer,
        db.ForeignKey("locations.location_id"),
        nullable=False
    )

    min_salary = db.Column(db.Float, nullable=False)
    midpoint_salary = db.Column(db.Float, nullable=False)
    max_salary = db.Column(db.Float, nullable=False)

    currency_code = db.Column(db.String(5), nullable=False)

    effective_from = db.Column(db.Date, nullable=False)
    effective_to = db.Column(db.Date, nullable=True)

    def __repr__(self):
        return f"<CompensationBand {self.band_id}>"