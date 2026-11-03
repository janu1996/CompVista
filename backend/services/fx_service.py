
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from models import FXRate


def get_historical_fx_rate(from_currency, to_currency, effective_date):
    source = str(from_currency or "").strip().upper()
    target = str(to_currency or "").strip().upper()

    if not source or not target:
        raise ValueError("Source and target currencies are required.")

    if isinstance(effective_date, str):
        try:
            effective_date = date.fromisoformat(effective_date)
        except ValueError:
            raise ValueError("Invalid effective date. Use YYYY-MM-DD.")

    if not isinstance(effective_date, date):
        raise ValueError("Effective date must be a date or YYYY-MM-DD string.")

    if source == target:
        return Decimal("1.000000")

    matching_rates = FXRate.query.filter(
        FXRate.from_currency == source,
        FXRate.to_currency == target,
        FXRate.effective_from <= effective_date,
        (
            FXRate.effective_to.is_(None)
            | (FXRate.effective_to > effective_date)
        )
    ).order_by(FXRate.effective_from.desc()).all()

    if not matching_rates:
        raise ValueError(
            f"No FX rate found for {source} to {target} "
            f"on {effective_date.isoformat()}."
        )

    if len(matching_rates) > 1:
        raise ValueError(
            f"Overlapping FX rates found for {source} to {target} "
            f"on {effective_date.isoformat()}. Resolve the overlapping "
            "effective periods before conversion."
        )

    rate = Decimal(str(matching_rates[0].rate))

    if not rate.is_finite() or rate <= 0:
        raise ValueError("FX rate must be a positive finite number.")

    return rate


def convert_to_inr(amount, currency_code, effective_date):
    try:
        original_amount = Decimal(str(amount))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("Amount must be a valid numeric value.")

    if not original_amount.is_finite() or original_amount < 0:
        raise ValueError("Amount must be a finite non-negative value.")

    source = str(currency_code or "").strip().upper()

    if not source:
        raise ValueError("Currency code is required.")

    rate = get_historical_fx_rate(
        source,
        "INR",
        effective_date
    )

    converted = (
        original_amount * rate
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    if isinstance(effective_date, str):
        conversion_date = date.fromisoformat(effective_date).isoformat()
    else:
        conversion_date = effective_date.isoformat()

    return {
        "original_amount": original_amount,
        "original_currency": source,
        "exchange_rate": rate,
        "target_currency": "INR",
        "converted_amount": converted,
        "conversion_date": conversion_date
    }
