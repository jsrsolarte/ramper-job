import hashlib
import re
import unicodedata

from django.utils.text import slugify


def vacancy_dedupe_key(source, external_id, title, company, location, original_url=""):
    stable_id = (external_id or "").strip()
    if stable_id.isdigit():
        identity = f"external:{stable_id}"
    else:
        normalized_title = _normalize(title)
        normalized_location = _normalize(location)
        normalized_company = _normalize(company)
        if normalized_title and normalized_location:
            identity = f"fingerprint:{normalized_title}|{normalized_company}|{normalized_location}"
        else:
            identity = f"url:{slugify(original_url)}"
    return hashlib.sha256(f"{source}:{identity}".encode("utf-8")).hexdigest()


def _normalize(value):
    value = unicodedata.normalize("NFKD", str(value or "").casefold())
    value = "".join(char for char in value if not unicodedata.combining(char))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value).split())
