"""Pure conversions for the transition from ten-point scores to stars."""
from decimal import Decimal, InvalidOperation, ROUND_CEILING, ROUND_HALF_UP


_HALF = Decimal('0.5')


def _decimal(value):
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError('El puntaje debe ser numérico.') from None
    if isinstance(value, bool) or not number.is_finite():
        raise ValueError('El puntaje debe ser numérico y finito.')
    return number


def rounded_star_score(value):
    """Clamp a star total to 0–5 and round to half stars, ties upward."""
    total = max(Decimal('0'), min(Decimal('5'), _decimal(value)))
    return (total / _HALF).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * _HALF


def historical_score_to_stars(value):
    """Convert a valid historic 0–10 score without discarding its source value."""
    score = _decimal(value)
    if not Decimal('0') <= score <= Decimal('10'):
        raise ValueError('El puntaje histórico debe estar entre 0 y 10.')
    return rounded_star_score(score / Decimal('2'))


def historical_profile_minimum(value):
    """Convert a historic profile threshold to whole stars, rounding upward."""
    minimum = _decimal(value)
    if not Decimal('0') <= minimum <= Decimal('10') or minimum != minimum.to_integral_value():
        raise ValueError('El mínimo histórico debe ser un entero entre 0 y 10.')
    return int((minimum / Decimal('2')).to_integral_value(rounding=ROUND_CEILING))


def calculate_star_total(criterion_points, deductions):
    """Sum and deduct in full precision before clamping and rounding once."""
    values = [_decimal(value) for value in criterion_points]
    penalties = [_decimal(value) for value in deductions]
    if any(value < 0 for value in values + penalties):
        raise ValueError('Los puntos y las deducciones no pueden ser negativos.')
    return rounded_star_score(sum(values, Decimal('0')) - sum(penalties, Decimal('0')))


def meets_captured_legacy_threshold(raw_stars, legacy_threshold):
    """Compare an unrounded new score with a previously captured 0–10 threshold."""
    score = _decimal(raw_stars)
    threshold = _decimal(legacy_threshold)
    if not Decimal('0') <= threshold <= Decimal('10') or threshold != threshold.to_integral_value():
        raise ValueError('El umbral histórico debe ser un entero entre 0 y 10.')
    if not Decimal('0') <= score <= Decimal('5'):
        raise ValueError('El puntaje sin redondear debe estar entre 0 y 5.')
    return score >= threshold / Decimal('2')
