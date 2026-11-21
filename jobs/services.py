from dataclasses import dataclass, replace
import uuid
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from datetime import datetime, time

from .connectors.base import JobListing
from .identity import normalize_vacancy_url, normalized_url_hash, vacancy_dedupe_key
from .models import Vacancy, VacancyDetailLease, VacancyURLAlias

DETAIL_FETCH_LEASE = timedelta(minutes=20)


@dataclass(frozen=True)
class ListingSaveSummary:
    vacancies: list[Vacancy]
    new_count: int
    known_count: int
    known_updated_count: int
    known_unchanged_count: int


def canonicalize_url(url: str) -> str:
    return normalize_vacancy_url(url)


@transaction.atomic
def save_listing(listing: JobListing, *, details_confirmed=False) -> tuple[Vacancy, bool]:
    canonical_url = canonicalize_url(listing.original_url)
    dedupe_key = vacancy_dedupe_key(
        listing.source, listing.external_id, listing.title, listing.company,
        listing.location, canonical_url,
    )
    canonical_hash = normalized_url_hash(canonical_url)
    raw_data = dict(listing.raw_data or {})
    details_confirmed = details_confirmed or (raw_data.get("details_fetch") or {}).get("status") == "confirmed"
    if details_confirmed:
        raw_data["details_fetch"] = {
            **(raw_data.get("details_fetch") or {}),
            "status": "confirmed",
            "confirmed_at": (raw_data.get("details_fetch") or {}).get("confirmed_at") or timezone.now().isoformat(),
        }
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
        "normalized_url": canonical_url,
        "normalized_url_hash": canonical_hash,
        "title": listing.title.strip(),
        "company": listing.company or None,
        "location": listing.location or None,
        "description": listing.description or None,
        # Keep the source's full structured evidence in raw_data while bounding
        # these summary columns to the lengths defined by the database schema.
        "salary": (listing.salary or "")[:200] or None,
        "contract_type": (listing.contract_type or "")[:200] or None,
        "raw_data": raw_data,
        "availability_status": Vacancy.AvailabilityStatus.ACTIVE,
        "last_seen_at": timezone.now(),
        "published_at": published_at,
        "is_active": True,
        "details_status": Vacancy.DetailStatus.CONFIRMED if details_confirmed else Vacancy.DetailStatus.UNKNOWN,
        "details_confirmed_at": timezone.now() if details_confirmed else None,
    }
    vacancy = Vacancy.objects.filter(
        source=listing.source, normalized_url_hash=canonical_hash, normalized_url=canonical_url,
    ).first()
    if vacancy is None:
        alias = VacancyURLAlias.objects.select_related("vacancy").filter(
            source=listing.source, normalized_url_hash=canonical_hash, normalized_url=canonical_url,
        ).first()
        vacancy = alias.vacancy if alias else None
    if vacancy is None:
        vacancy, created = Vacancy.objects.get_or_create(
            source=listing.source,
            normalized_url_hash=canonical_hash,
            defaults={**defaults, "original_url": canonical_url},
        )
        if not created and vacancy.normalized_url != canonical_url:
            raise ValueError("Se detectó una colisión al calcular la identidad de la URL.")
    else:
        created = False
    materially_changed = created
    if not created:
        preserve_confirmed_details = (
            vacancy.details_status == Vacancy.DetailStatus.CONFIRMED and not details_confirmed
        )
        previous_material = tuple(getattr(vacancy, field) for field in (
            "title", "company", "location", "description", "salary", "contract_type"
        )) + ((vacancy.raw_data or {}).get("details") or {},)
        incoming_raw_data = dict(raw_data)
        if preserve_confirmed_details:
            incoming_raw_data.pop("details", None)
            incoming_raw_data.pop("details_fetch", None)
        raw_data = {**(vacancy.raw_data or {}), **incoming_raw_data}
        existing_details = (vacancy.raw_data or {}).get("details") or {}
        incoming_details = incoming_raw_data.get("details") or {}
        if preserve_confirmed_details:
            raw_data["details"] = existing_details
        elif existing_details or incoming_details:
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
        if preserve_confirmed_details:
            for field in ("company", "location", "description", "salary", "contract_type"):
                defaults[field] = getattr(vacancy, field)
            defaults["details_status"] = vacancy.details_status
            defaults["details_confirmed_at"] = vacancy.details_confirmed_at
        elif not details_confirmed:
            defaults["details_status"] = vacancy.details_status
            defaults["details_confirmed_at"] = vacancy.details_confirmed_at
        for field, value in defaults.items():
            if value is None and field in {"company", "location", "description", "salary", "contract_type", "external_id", "published_at"}:
                continue
            setattr(vacancy, field, value)
        current_material = tuple(getattr(vacancy, field) for field in (
            "title", "company", "location", "description", "salary", "contract_type"
        )) + ((vacancy.raw_data or {}).get("details") or {},)
        materially_changed = previous_material != current_material
        vacancy.save(update_fields=[*defaults.keys()])
    if canonical_url != vacancy.normalized_url:
        VacancyURLAlias.objects.get_or_create(
            source=listing.source,
            normalized_url=canonical_url,
            normalized_url_hash=canonical_hash,
            defaults={"vacancy": vacancy},
        )
    requested_url = (raw_data.get("details_fetch") or {}).get("requested_url")
    if requested_url:
        requested_normalized = canonicalize_url(requested_url)
        if requested_normalized != vacancy.normalized_url:
            requested_hash = normalized_url_hash(requested_normalized)
            alias, alias_created = VacancyURLAlias.objects.get_or_create(
                source=listing.source,
                normalized_url_hash=requested_hash,
                defaults={"normalized_url": requested_normalized, "vacancy": vacancy},
            )
            if not alias_created and (alias.normalized_url != requested_normalized or alias.vacancy_id != vacancy.pk):
                raise ValueError("La URL solicitada ya está asociada a otra ficha.")
    vacancy._materially_changed = materially_changed
    return vacancy, created


def save_listings(listings: list[JobListing], *, details_confirmed=False) -> ListingSaveSummary:
    """Persist listings and classify each distinct vacancy once for this query."""
    outcomes = {}
    for listing in listings:
        confirmed = details_confirmed or (listing.raw_data or {}).get("details_fetch", {}).get("status") == "confirmed"
        vacancy, created = save_listing(listing, details_confirmed=confirmed)
        outcome = outcomes.setdefault(vacancy.pk, {
            "vacancy": vacancy,
            "created": False,
            "materially_changed": False,
        })
        outcome["created"] = outcome["created"] or created
        outcome["materially_changed"] = outcome["materially_changed"] or getattr(
            vacancy, "_materially_changed", True
        )

    new_count = 0
    known_count = 0
    known_updated_count = 0
    known_unchanged_count = 0
    for outcome in outcomes.values():
        outcome["vacancy"]._materially_changed = outcome["materially_changed"]
        if outcome["created"]:
            new_count += 1
        else:
            known_count += 1
            if outcome["materially_changed"]:
                known_updated_count += 1
            else:
                known_unchanged_count += 1
    return ListingSaveSummary(
        vacancies=[outcome["vacancy"] for outcome in outcomes.values()],
        new_count=new_count,
        known_count=known_count,
        known_updated_count=known_updated_count,
        known_unchanged_count=known_unchanged_count,
    )


def find_vacancy_for_url(source, url):
    normalized = canonicalize_url(url)
    url_hash = normalized_url_hash(normalized)
    vacancy = Vacancy.objects.filter(
        source=source, normalized_url_hash=url_hash, normalized_url=normalized,
    ).first()
    if vacancy:
        return vacancy
    alias = VacancyURLAlias.objects.select_related("vacancy").filter(
        source=source, normalized_url_hash=url_hash, normalized_url=normalized,
    ).first()
    return alias.vacancy if alias else None


def confirmed_listing_details(listing):
    vacancy = find_vacancy_for_url(listing.source, listing.original_url)
    if vacancy is None or vacancy.details_status != Vacancy.DetailStatus.CONFIRMED:
        return None
    raw_data = dict(vacancy.raw_data or {})
    return replace(
        listing,
        external_id=vacancy.external_id or listing.external_id,
        title=vacancy.title,
        company=vacancy.company,
        location=vacancy.location,
        description=vacancy.description,
        original_url=vacancy.original_url,
        raw_data=raw_data,
        salary=vacancy.salary,
        contract_type=vacancy.contract_type,
    )


@transaction.atomic
def claim_detail_fetch(source, url, *, token=None, now=None):
    """Claim a source/URL detail request without coupling it to a batch or vacancy row."""
    from django.utils import timezone

    now = now or timezone.now()
    token = token or uuid.uuid4().hex
    normalized = canonicalize_url(url)
    url_hash = normalized_url_hash(normalized)
    VacancyDetailLease.objects.get_or_create(
        source=source,
        normalized_url_hash=url_hash,
        defaults={"normalized_url": normalized},
    )
    lease = VacancyDetailLease.objects.select_for_update().get(source=source, normalized_url_hash=url_hash)
    if lease.normalized_url != normalized:
        raise ValueError("Se detectó una colisión al calcular la identidad de la URL.")
    if lease.token and lease.expires_at and lease.expires_at > now and lease.token != token:
        return "busy", ""
    lease.token = token
    lease.expires_at = now + DETAIL_FETCH_LEASE
    lease.save(update_fields=("token", "expires_at", "updated_at"))
    return "claimed", token


def release_detail_fetch_leases(*, token, url_hashes):
    if not token or not url_hashes:
        return 0
    return VacancyDetailLease.objects.filter(
        normalized_url_hash__in=set(url_hashes), token=token,
    ).update(token="", expires_at=None, updated_at=timezone.now())
