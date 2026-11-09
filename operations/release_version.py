"""Validation helpers for immutable production release versions."""

from __future__ import annotations

import re

_VERSION_TAG = re.compile(r"^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")


class ReleaseVersionError(ValueError):
    """Raised when a release tag violates the repository's version policy."""


def validate_release_tag(tag: str, existing_tags: list[str]) -> tuple[int, int, int]:
    """Validate a stable vMAJOR.MINOR.PATCH tag and return its numeric version."""
    match = _VERSION_TAG.fullmatch(tag)
    if not match:
        raise ReleaseVersionError(
            f"Invalid release tag {tag!r}; expected vMAJOR.MINOR.PATCH without leading zeros."
        )

    if tag in existing_tags:
        raise ReleaseVersionError(f"Release tag {tag} already exists and cannot be reused.")

    version = tuple(int(part) for part in match.groups())
    existing_versions = [
        candidate
        for existing in existing_tags
        if (candidate := _VERSION_TAG.fullmatch(existing)) is not None
    ]
    if not existing_versions and version != (1, 0, 0):
        raise ReleaseVersionError("The first production release must be v1.0.0.")

    return version
