from decimal import Decimal, ROUND_HALF_UP


def _rounded_half_star_units(score):
    value = Decimal(str(score)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return max(0, min(10, int(value)))


def score_star_percent(score):
    """Return the fill percentage after rounding the visual score to half-stars."""
    return _rounded_half_star_units(score) * 10


def score_star_label(score):
    """Return a localized 0–5 star value while preserving exact scores elsewhere."""
    stars = Decimal(_rounded_half_star_units(score)) / Decimal("2")
    return f"{stars:.1f}".replace(".", ",")


def score_star_threshold_label(score):
    """Return a concise localized star threshold for score filter controls."""
    label = score_star_label(score)
    label = label[:-2] if label.endswith(",0") else label
    noun = "estrella" if label == "1" else "estrellas"
    return f"{label} {noun}"
