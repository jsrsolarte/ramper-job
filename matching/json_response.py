"""Conservative parsing for JSON objects returned by model providers."""

import json
import re


MAX_MODEL_JSON_CHARS = 1_000_000
_FULL_CODE_BLOCK = re.compile(
    r"\A\s*```(?:json)?[ \t]*\r?\n(?P<body>[\s\S]*?)\r?\n```[ \t]*\s*\Z",
    re.IGNORECASE,
)


class ModelJSONParseError(ValueError):
    """A safe, content-free parsing error with optional repair metadata."""

    def __init__(self, category, *, repair_candidate=None, repair_allowed=False):
        self.category = category
        self.repair_candidate = repair_candidate
        self.repair_allowed = repair_allowed
        super().__init__("OmniRoute devolvió contenido que no es un objeto JSON válido.")


def parse_model_json_object(content, *, max_chars=MAX_MODEL_JSON_CHARS):
    """Parse an object directly or from one complete, unambiguous Markdown fence.

    No substring extraction is performed. Invalid syntax is marked repairable only
    for direct content or the body of one complete fence; valid non-object JSON,
    oversized content, and ambiguous Markdown are rejected without repair.
    """
    return parse_model_json_object_with_action(content, max_chars=max_chars)[0]


def parse_model_json_object_with_action(content, *, max_chars=MAX_MODEL_JSON_CHARS):
    if isinstance(content, dict):
        try:
            serialized = json.dumps(content, ensure_ascii=False, separators=(",", ":"))
        except (TypeError, ValueError):
            raise ModelJSONParseError("omniroute.invalid_shape") from None
        if len(serialized) > max_chars:
            raise ModelJSONParseError("omniroute.invalid_shape")
        return content, "direct"
    if not isinstance(content, str) or len(content) > max_chars:
        raise ModelJSONParseError("omniroute.invalid_shape")

    direct = _decode_json(content)
    if direct is not _INVALID:
        if isinstance(direct, dict):
            return direct, "direct"
        raise ModelJSONParseError("omniroute.invalid_shape")

    fenced = _FULL_CODE_BLOCK.fullmatch(content)
    if fenced:
        candidate = fenced.group("body")
        if "```" in candidate:
            raise ModelJSONParseError("omniroute.ambiguous_content")
        parsed = _decode_json(candidate)
        if parsed is not _INVALID:
            if isinstance(parsed, dict):
                return parsed, "normalized"
            raise ModelJSONParseError("omniroute.invalid_shape")
        raise ModelJSONParseError(
            "omniroute.invalid_json", repair_candidate=candidate, repair_allowed=True
        )

    if "```" in content:
        raise ModelJSONParseError("omniroute.ambiguous_content")
    raise ModelJSONParseError(
        "omniroute.invalid_json", repair_candidate=content, repair_allowed=True
    )


_INVALID = object()


def _decode_json(value):
    try:
        return json.loads(value, object_pairs_hook=_unique_object)
    except (json.JSONDecodeError, TypeError, ValueError):
        return _INVALID


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def repair_preserves_values(original, repaired):
    """Accept only output equal to a narrowly recoverable syntax-only form."""
    recovered = _recover_simple_json_syntax(original)
    return recovered is not _INVALID and _same_json_value(recovered, repaired)


def _recover_simple_json_syntax(value):
    candidate = value
    for _ in range(4):
        parsed = _decode_json(candidate)
        if isinstance(parsed, dict):
            return parsed
        without_trailing_commas = _sub_outside_json_strings(
            r",\s*([}\]])", r"\1", candidate
        )
        if without_trailing_commas != candidate:
            candidate = without_trailing_commas
            continue
        with_missing_commas = _sub_outside_json_strings(
            r'("(?:\\.|[^"\\])*")\s+("(?:\\.|[^"\\])*"\s*:)',
            r"\1,\2",
            candidate,
        )
        if with_missing_commas != candidate:
            candidate = with_missing_commas
            continue
        with_missing_commas = _sub_outside_json_strings(
            r'(true|false|null|-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?|[}\]])\s+("(?:\\.|[^"\\])*"\s*:)',
            r"\1,\2",
            candidate,
        )
        if with_missing_commas != candidate:
            candidate = with_missing_commas
            continue
        break
    parsed = _decode_json(candidate)
    return parsed if isinstance(parsed, dict) else _INVALID


def _sub_outside_json_strings(pattern, replacement, value):
    """Apply a recovery pattern only when its match starts outside a JSON string.

    Recovery patterns may include complete quoted keys. Checking the start position
    lets those tokens participate while preventing a matching substring inside a
    value literal from being rewritten.
    """
    outside = _outside_json_strings(value)
    matches = list(re.finditer(pattern, value))
    if not matches:
        return value
    pieces = []
    position = 0
    for match in matches:
        if not outside[match.start()]:
            continue
        pieces.append(value[position:match.start()])
        pieces.append(match.expand(replacement))
        position = match.end()
    if not pieces:
        return value
    pieces.append(value[position:])
    return "".join(pieces)


def _outside_json_strings(value):
    """Return a per-character mask that is false inside strings, honoring escapes."""
    outside = [True] * len(value)
    in_string = False
    escaped = False
    for index, char in enumerate(value):
        outside[index] = not in_string
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
    return outside


def _same_json_value(left, right):
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(_same_json_value(left[key], right[key]) for key in left)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(_same_json_value(a, b) for a, b in zip(left, right))
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left == right
    return type(left) is type(right) and left == right
