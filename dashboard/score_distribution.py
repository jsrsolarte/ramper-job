from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


MINIMUM_RECOMMENDATION_SAMPLE = 5


def build_score_summary(scores, *, minimum_score=0):
    """Build one-point score bands and a reproducible median suggestion."""
    values = []
    for score in scores:
        try:
            value = Decimal(str(score))
        except (InvalidOperation, TypeError, ValueError):
            continue
        if value.is_finite() and Decimal("0") <= value <= Decimal("10"):
            values.append(value)

    values.sort()
    sample_size = len(values)
    maximum_count = 0
    bands = []
    for lower in range(10):
        upper = lower + 1
        if upper == 10:
            count = sum(1 for value in values if lower <= value <= Decimal("10"))
            label = f"{lower}–10"
        else:
            count = sum(1 for value in values if lower <= value < upper)
            label = f"{lower}–<{upper}"
        maximum_count = max(maximum_count, count)
        bands.append({"label": label, "count": count})

    suggested_score = None
    suggested_count = 0
    if sample_size >= MINIMUM_RECOMMENDATION_SAMPLE:
        middle = sample_size // 2
        if sample_size % 2:
            median = values[middle]
        else:
            median = (values[middle - 1] + values[middle]) / Decimal("2")
        suggested_score = int(median.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        suggested_count = sum(1 for value in values if value >= suggested_score)

    for band in bands:
        band["width_percent"] = round(band["count"] * 100 / maximum_count) if maximum_count else 0

    return {
        "bands": bands,
        "sample_size": sample_size,
        "maximum_count": maximum_count,
        "suggested_score": suggested_score,
        "suggested_count": suggested_count,
        "suggestion_below_profile": (
            suggested_score is not None and suggested_score < minimum_score
        ),
    }
