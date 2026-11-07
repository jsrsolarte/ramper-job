from dataclasses import dataclass, field
from typing import Protocol


class SourceUnavailable(Exception):
    """The public source cannot currently be queried."""


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


class JobSourceConnector(Protocol):
    source: str

    def fetch(
        self,
        keywords: list[str],
        locations: list[str] | None = None,
        *,
        remote_ok: bool = False,
    ) -> list[JobListing]: ...
