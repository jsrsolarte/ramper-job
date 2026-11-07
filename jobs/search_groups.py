import hashlib
import json


def _normalized_values(values):
    normalized = {}
    for value in values or []:
        display_value = " ".join(str(value or "").split())
        key = display_value.casefold()
        if key:
            normalized.setdefault(key, display_value)
    return normalized


def search_request_identity(connector, request):
    """Return a stable identity for source requests with equivalent inputs."""
    keywords = _normalized_values(request.get("keywords"))
    locations = _normalized_values(request.get("locations"))
    connector_type = f"{type(connector).__module__}.{type(connector).__qualname__}"
    identity = {
        "source": str(connector.source).strip().casefold(),
        "connector": connector_type,
        "keywords": sorted(keywords),
        "locations": sorted(locations),
        "remote_ok": bool(request.get("remote_ok")),
        "matching_config_id": request.get("matching_config_id"),
    }
    encoded = json.dumps(identity, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def group_search_requests(connector, requests):
    groups = {}
    for request in requests:
        key = search_request_identity(connector, request)
        group = groups.setdefault(key, {"request": request, "members": []})
        group["members"].append(request)
    return list(groups.values())
