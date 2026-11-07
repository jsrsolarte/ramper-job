from urllib.parse import urlsplit, urlunsplit

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from datetime import datetime, time

from .connectors.base import JobListing
from .identity import vacancy_dedupe_key
from .models import Vacancy


def canonicalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, "", ""))


@transaction.atomic
def save_listing(listing: JobListing) -> tuple[Vacancy, bool]:
    canonical_url = canonicalize_url(listing.original_url)
    dedupe_key = vacancy_dedupe_key(
        listing.source, listing.external_id, listing.title, listing.company,
        listing.location, canonical_url,
    )
    raw_data = listing.raw_data or {}
    published_at = parse_datetime(str(raw_data.get("datePosted", "")))
    if published_at is None:
        details = raw_data.get("details") or {}
        posted_date = parse_date(str(details.get("date_posted", "")))
        if posted_date:
            published_at = datetime.combine(posted_date, time.min)
    if published_at and timezone.is_naive(published_at):
        published_at = timezone.make_aware(published_at)
    defaults = {
        "external_id": listing.external_id or None,
        "dedupe_key": dedupe_key,
        "title": listing.title.strip(),
        "company": listing.company or None,
        "location": listing.location or None,
        "description": listing.description or None,
        # Keep the source's full structured evidence in raw_data while bounding
        # these summary columns to the lengths defined by the database schema.
        "salary": (listing.salary or "")[:200] or None,
        "contract_type": (listing.contract_type or "")[:200] or None,
        "raw_data": listing.raw_data or {},
        "availability_status": Vacancy.AvailabilityStatus.ACTIVE,
        "last_seen_at": timezone.now(),
        "published_at": published_at,
        "is_active": True,
    }
    vacancy = Vacancy.objects.filter(source=listing.source, original_url=canonical_url).first()
    if vacancy is None:
        vacancy, created = Vacancy.objects.get_or_create(
            source=listing.source,
            dedupe_key=dedupe_key,
            defaults={**defaults, "original_url": canonical_url},
        )
    else:
        created = False
    materially_changed = created
    if not created:
        previous_material = tuple(getattr(vacancy, field) for field in (
            "title", "company", "location", "description", "salary", "contract_type"
        )) + ((vacancy.raw_data or {}).get("details") or {},)
        incoming_raw_data = dict(listing.raw_data or {})
        raw_data = {**(vacancy.raw_data or {}), **incoming_raw_data}
        existing_details = (vacancy.raw_data or {}).get("details") or {}
        incoming_details = incoming_raw_data.get("details") or {}
        if existing_details or incoming_details:
            raw_data["details"] = {
                **existing_details,
                **{key: value for key, value in incoming_details.items() if value not in (None, "", [])},
            }
        alternate_urls = list(raw_data.get("alternate_urls", []))
        if canonical_url != vacancy.original_url and canonical_url not in alternate_urls:
            alternate_urls.append(canonical_url)
        if alternate_urls:
            raw_data["alternate_urls"] = alternate_urls
        defaults["raw_data"] = raw_data
        for field, value in defaults.items():
            if value is None and field in {"company", "location", "description", "salary", "contract_type", "external_id", "published_at"}:
                continue
            setattr(vacancy, field, value)
        current_material = tuple(getattr(vacancy, field) for field in (
            "title", "company", "location", "description", "salary", "contract_type"
        )) + ((vacancy.raw_data or {}).get("details") or {},)
        materially_changed = previous_material != current_material
        vacancy.save(update_fields=[*defaults.keys()])
    vacancy._materially_changed = materially_changed
    return vacancy, created


def save_listings(listings: list[JobListing]) -> list[Vacancy]:
    return [save_listing(listing)[0] for listing in listings]
