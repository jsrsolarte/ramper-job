from dataclasses import dataclass, field
from typing import Protocol


class SourceUnavailable(Exception):
    """The public source cannot currently be queried."""


class SourcePartiallyUnavailable(SourceUnavailable):
    """A source became unavailable after returning usable listing data."""

    def __init__(self, message, listings):
        super().__init__(message)
        self.listings = list(listings)


@dataclass(frozen=True)
class JobListing:
    source: str
    external_id: str
    title: str
    company: str | None
    location: str | None
    description: str | None
    original_url: str
    raw_data: dict = field(default_factory=dict)
    salary: str | None = None
    contract_type: str | None = None


def mark_details_confirmed(listing, *, requested_url=None):
    """Attach per-listing success evidence only after parsing a detail response."""
    from dataclasses import replace

    raw_data = dict(listing.raw_data or {})
    evidence = {"status": "confirmed"}
    if requested_url:
        evidence["requested_url"] = requested_url
    raw_data["details_fetch"] = evidence
    return replace(listing, raw_data=raw_data)


class JobSourceConnector(Protocol):
    source: str

    def fetch(
        self,
        keywords: list[str],
        locations: list[str] | None = None,
        *,
        remote_ok: bool = False,
    ) -> list[JobListing]: ...
