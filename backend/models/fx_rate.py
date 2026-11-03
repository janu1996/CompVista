
from extensions import db
from sqlalchemy import Numeric, UniqueConstraint


class FXRate(db.Model):
    __tablename__ = "fx_rates"

    __table_args__ = (
        db.CheckConstraint(
            "rate > 0",
            name="check_positive_fx_rate"
        ),
        db.CheckConstraint(
            "effective_to IS NULL OR effective_to > effective_from",
            name="check_valid_fx_dates"
        ),
        UniqueConstraint(
            "from_currency",
            "to_currency",
            "effective_from",
            name="unique_fx_rate_period"
        ),
    )

    fx_rate_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    from_currency = db.Column(
        db.String(5),
        nullable=False
    )

    to_currency = db.Column(
        db.String(5),
        nullable=False
    )

    rate = db.Column(
        Numeric(14, 6),
        nullable=False
    )

    effective_from = db.Column(
        db.Date,
        nullable=False
    )

    effective_to = db.Column(
        db.Date,
        nullable=True
    )

    source = db.Column(
        db.String(100),
        nullable=False,
        default="SYNTHETIC_DATASET"
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    def __repr__(self):
        return (
            f"<FXRate {self.from_currency}/"
            f"{self.to_currency}: {self.rate}>"
        )
