import unicodedata


MEDELLIN_AREA = (
    "Medellín",
    "Bello",
    "Envigado",
    "Itagüí",
    "Sabaneta",
    "La Estrella",
    "Caldas",
    "Copacabana",
    "Girardota",
    "Barbosa",
)

BOGOTA_AREA = (
    "Bogotá",
    "Soacha",
    "Chía",
    "Cajicá",
    "Cota",
    "Funza",
    "Madrid",
    "Mosquera",
    "La Calera",
    "Tenjo",
    "Facatativá",
    "Zipaquirá",
)


def _normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    unaccented = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join("".join(char if char.isalnum() else " " for char in unaccented).split())


_AREA_ALIASES = {
    _normalize(alias): MEDELLIN_AREA
    for alias in ("Medellín", "Medellín, Antioquia", "Valle de Aburrá")
}
_AREA_ALIASES.update({
    _normalize(alias): BOGOTA_AREA
    for alias in ("Bogotá", "Bogotá D.C.", "Bogotá alrededores", "Bogota y alrededores")
})


def expand_locations(locations: list[str] | None) -> list[str]:
    """Expand selected Colombian city groups while preserving user order."""
    expanded = []
    seen = set()
    for location in locations or []:
        if not isinstance(location, str) or not location.strip():
            continue
        options = _AREA_ALIASES.get(_normalize(location), (" ".join(location.split()),))
        for option in options:
            key = _normalize(option)
            if key not in seen:
                expanded.append(option)
                seen.add(key)
    return expanded


def vacancy_location_is_eligible(vacancy, profile_revision) -> bool:
    """Return whether a vacancy's published location fits one profile revision."""
    details = (vacancy.raw_data or {}).get("details") or {}
    modality = _normalize(str(details.get("modality") or ""))
    remote = modality in {"remoto", "teletrabajo"}
    if remote:
        return bool(profile_revision.remote_ok)

    preferences = expand_locations(profile_revision.locations)
    if not preferences:
        return True
    actual_city = details.get("city")
    actual_location = _normalize(str(actual_city or vacancy.location or ""))
    if not actual_location:
        return not preferences

    return any(
        actual_location == _normalize(preferred)
        or _normalize(preferred) in actual_location
        for preferred in preferences
    )
