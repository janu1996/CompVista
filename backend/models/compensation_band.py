
from extensions import db
from sqlalchemy import Numeric


class CompensationBand(db.Model):
    __tablename__ = "compensation_bands"

    # Database validations
    __table_args__ = (
        db.CheckConstraint(
            "min_salary < midpoint_salary AND midpoint_salary < max_salary",
            name="check_valid_salary_band"
        ),
        db.CheckConstraint(
            "effective_to IS NULL OR effective_to > effective_from",
            name="check_valid_band_dates"
        ),
    )

    # Primary Key
    band_id = db.Column(
        db.String(100),
        primary_key=True
    )

    # Foreign Keys
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

    # Salary Range
    min_salary = db.Column(
        Numeric(14, 2),
        nullable=False
    )

    midpoint_salary = db.Column(
        Numeric(14, 2),
        nullable=False
    )

    max_salary = db.Column(
        Numeric(14, 2),
        nullable=False
    )

    # Currency
    currency_code = db.Column(
        db.String(5),
        nullable=False
    )

    # Effective Dates
    effective_from = db.Column(
        db.Date,
        nullable=False
    )

    effective_to = db.Column(
        db.Date,
        nullable=True
    )

    def __repr__(self):
        return f"<CompensationBand {self.band_id}>"
