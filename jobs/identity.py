import hashlib
from urllib.parse import urlsplit, urlunsplit

def vacancy_dedupe_key(source, external_id, title, company, location, original_url=""):
    identity = normalize_vacancy_url(original_url)
    return hashlib.sha256(f"{source}:{identity}".encode("utf-8")).hexdigest()


def normalized_url_hash(url):
    return hashlib.sha256(normalize_vacancy_url(url).encode("utf-8")).hexdigest()


def normalize_vacancy_url(url):
    """Canonical identity for a public vacancy URL, excluding tracking data."""
    try:
        parts = urlsplit(str(url or "").strip())
        scheme = parts.scheme.lower()
        host = (parts.hostname or "").rstrip(".").encode("idna").decode("ascii").lower()
        port = parts.port
    except (UnicodeError, ValueError) as exc:
        raise ValueError("La URL de la vacante no es válida.") from exc
    if scheme not in {"http", "https"} or not host or parts.username or parts.password:
        raise ValueError("La URL de la vacante debe usar HTTP(S) y un host público válido.")
    if port and not (1 <= port <= 65535):
        raise ValueError("El puerto de la URL no es válido.")
    netloc = f"[{host}]" if ":" in host else host
    if port and not (scheme == "http" and port == 80 or scheme == "https" and port == 443):
        netloc = f"{netloc}:{port}"
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((scheme, netloc, path, "", ""))
