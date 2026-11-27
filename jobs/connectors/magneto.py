"""Safe public-page connector for Magneto Colombia vacancy listings."""

import json
import ipaddress
import re
import socket
import time
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.utils.text import slugify

from jobs.identity import vacancy_dedupe_key

from .base import JobListing, SourcePartiallyUnavailable, SourceUnavailable, mark_details_confirmed


MAGNETO_HOSTS = {"www.magneto365.com"}
MAGNETO_DETAIL_PATH = re.compile(r"^/co/empleos/[^/:?#]+/?$", re.IGNORECASE)
MAGNETO_BLOCK_STATUSES = {401, 403, 429}
MAGNETO_REDIRECT_STATUSES = {301, 302, 303, 307, 308}
MAGNETO_LOCATION_ROUTES = {
    # Medellín and Bogotá use the path shape from the shared capture/UI.
    "medellin": ("medellin-antioquia", "split_term_recency"),
    "medellin antioquia": ("medellin-antioquia", "split_term_recency"),
    "bogota": ("bogota-d.c.-bogota-d.c.", "split_term_recency"),
    "bogota d c": ("bogota-d.c.-bogota-d.c.", "split_term_recency"),
    # These municipalities were selected in Magneto's public location picker.
    "bello": ("bello-antioquia", "joined_term_recency"),
    "envigado": ("envigado-antioquia", "joined_term_recency"),
    "itagui": ("itagui-antioquia", "joined_term_recency"),
    "sabaneta": ("sabaneta-antioquia", "joined_term_recency"),
    "la estrella": ("la-estrella-antioquia", "joined_term_recency"),
    "caldas": ("caldas-antioquia", "joined_term_recency"),
    "copacabana": ("copacabana-antioquia", "joined_term_recency"),
    "girardota": ("girardota-antioquia", "joined_term_recency"),
    "barbosa": ("barbosa-antioquia", "joined_term_recency"),
    "soacha": ("soacha-cundinamarca", "joined_term_recency"),
    "chia": ("chia-cundinamarca", "joined_term_recency"),
    "cajica": ("cajica-cundinamarca", "joined_term_recency"),
    "cota": ("cota-cundinamarca", "joined_term_recency"),
    "funza": ("funza-cundinamarca", "joined_term_recency"),
    "madrid": ("madrid-cundinamarca", "joined_term_recency"),
    "mosquera": ("mosquera-cundinamarca", "joined_term_recency"),
    "la calera": ("la-calera-cundinamarca", "joined_term_recency"),
    "tenjo": ("tenjo-cundinamarca", "joined_term_recency"),
    "facatativa": ("facatativa-cundinamarca", "joined_term_recency"),
    "zipaquira": ("zipaquira-cundinamarca", "joined_term_recency"),
}


def validate_magneto_vacancy_url(url: str) -> str:
    """Validate and normalize a public Magneto Colombia vacancy URL."""
    parsed = urlparse((url or "").strip())
    if parsed.scheme.lower() != "https" or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError("La URL pública de Magneto debe usar HTTPS.")
    host = (parsed.hostname or "").lower()
    if host not in MAGNETO_HOSTS or not MAGNETO_DETAIL_PATH.fullmatch(parsed.path):
        raise ValueError("La URL no corresponde a una ficha pública de Magneto Colombia.")
    return urlunparse(("https", host, parsed.path.rstrip("/"), "", "", ""))


class MagnetoConnector:
    """Search Magneto's public Colombian listings and parse public detail pages."""

    source = "magneto_co"
    listing_url = "https://www.magneto365.com"

    def __init__(self, session=None):
        self.session = session or requests.Session()
        self.user_agent = settings.MAGNETO_USER_AGENT
        self.request_delay_seconds = 0.75
        self.request_timeout = (5, 20)
        self.max_redirects = 3
        self.status_message = ""

    def search_url(self, keyword: str, location: str | None = None) -> str:
        """Build a one-page recent query using route forms observed in captures."""
        term_slug = slugify(" ".join((keyword or "").split()))
        if not term_slug:
            raise ValueError("El término no produce una búsqueda válida en Magneto.")
        if location:
            location_key = self._normalize(location)
            route = MAGNETO_LOCATION_ROUTES.get(location_key)
            if not route:
                raise ValueError(f"No se ha verificado la ruta de Magneto para «{location}».")
            location_slug, route_shape = route
            if route_shape == "split_term_recency":
                path = f"/co/trabajos/buscar/loc-{location_slug}/{term_slug}/ultimos-3-dias"
            else:
                path = f"/co/trabajos/buscar/loc-{location_slug}/{term_slug}-ultimos-3-dias"
        else:
            path = f"/co/trabajos/buscar/ultimos-3-dias/{term_slug}"
        return f"{self.listing_url}{path}?order=desc_relevance"

    def fetch_titles(self, keywords, locations=None, *, remote_ok=False):
        """Fetch a single page for each supported term/location combination."""
        self.status_message = ""
        unique_keywords = list(dict.fromkeys(" ".join(term.split()) for term in keywords if term.strip()))
        if not unique_keywords:
            self.status_message = "El perfil no tiene palabras clave para consultar Magneto."
            return []
        unique_locations = list(dict.fromkeys(" ".join(value.split()) for value in locations or [] if value.strip()))
        queries = [(keyword, location) for keyword in unique_keywords for location in unique_locations]
        if remote_ok or not unique_locations:
            queries.extend((keyword, None) for keyword in unique_keywords)

        found = {}
        query_errors = []
        succeeded = 0
        requested = 0
        for keyword, location in queries:
            try:
                url = self.search_url(keyword, location)
            except ValueError as exc:
                query_errors.append(str(exc))
                continue
            if requested:
                time.sleep(self.request_delay_seconds)
            requested += 1
            try:
                response, final_url = self._get_public(url, detail=False)
            except SourceUnavailable as exc:
                if getattr(exc, "http_status", None) in MAGNETO_BLOCK_STATUSES:
                    message = "Magneto no permite continuar la consulta pública."
                    self.status_message = message
                    partial = list(found.values())
                    if partial:
                        raise SourcePartiallyUnavailable(message, partial) from None
                    raise SourceUnavailable(message) from None
                query_errors.append(f"No se pudo consultar «{keyword}» en Magneto.")
                continue
            except requests.RequestException:
                query_errors.append(f"No se pudo consultar «{keyword}» en Magneto.")
                continue
            succeeded += 1
            for listing in self.parse(response.text, final_url):
                key = vacancy_dedupe_key(
                    listing.source, listing.external_id, listing.title, listing.company,
                    listing.location, listing.original_url,
                )
                found.setdefault(key, listing)

        if not succeeded:
            message = query_errors[0] if query_errors else "No fue posible consultar Magneto."
            self.status_message = message[:300]
            raise SourceUnavailable(message)
        self.status_message = " ".join(query_errors)[:300]
        if query_errors:
            raise SourcePartiallyUnavailable(self.status_message, list(found.values()))
        return list(found.values())

    def fetch_details(self, listings):
        """Enrich unique URLs; stop on source blocks and preserve card data."""
        listings = list(listings)
        unique = {}
        for index, listing in enumerate(listings):
            unique.setdefault(listing.original_url, index)
        detail_errors = []
        requested = 0
        for url, index in unique.items():
            if requested:
                time.sleep(self.request_delay_seconds)
            requested += 1
            try:
                response, final_url = self._get_public(url, detail=True)
            except SourceUnavailable as exc:
                if getattr(exc, "http_status", None) in MAGNETO_BLOCK_STATUSES:
                    message = "Magneto bloqueó la consulta de fichas; se conservaron los datos del listado."
                    self.status_message = " ".join(filter(None, (self.status_message, message)))[:300]
                    raise SourcePartiallyUnavailable(self.status_message, listings) from None
                detail_errors.append(f"No se pudo consultar una ficha pública de Magneto. {exc}")
                continue
            except requests.RequestException as exc:
                detail_errors.append(f"No se pudo consultar una ficha pública de Magneto. {type(exc).__name__}.")
                continue
            try:
                details = self.parse_detail(response.text, final_url)
                merged, confirmed = self.merge_details(listings[index], details)
            except (ValueError, TypeError, AttributeError):
                detail_errors.append("No se pudo interpretar una ficha pública de Magneto.")
                continue
            if confirmed:
                listings[index] = mark_details_confirmed(merged, requested_url=url)
            else:
                listings[index] = merged
                detail_errors.append("Se conservó el listado porque la identidad de una ficha era ambigua.")
        self.status_message = " ".join(filter(None, (self.status_message, *detail_errors)))[:300]
        return listings

    def fetch(self, keywords, locations=None, *, remote_ok=False):
        try:
            return self.fetch_details(self.fetch_titles(keywords, locations=locations, remote_ok=remote_ok))
        except SourcePartiallyUnavailable as exc:
            return exc.listings

    def _get_public(self, url, *, detail):
        try:
            current_url = validate_magneto_vacancy_url(url) if detail else self._validate_search_url(url)
        except ValueError as exc:
            raise SourceUnavailable(str(exc)) from None
        for redirect_count in range(self.max_redirects + 1):
            self._assert_public_host(current_url)
            response = self.session.get(
                current_url,
                headers={"User-Agent": self.user_agent},
                timeout=self.request_timeout,
                allow_redirects=False,
            )
            if response.status_code in MAGNETO_BLOCK_STATUSES:
                error = SourceUnavailable("Magneto rechazó la consulta pública.")
                error.http_status = response.status_code
                raise error
            if response.status_code in MAGNETO_REDIRECT_STATUSES:
                if redirect_count >= self.max_redirects:
                    raise SourceUnavailable("Magneto devolvió demasiadas redirecciones.")
                destination = response.headers.get("Location")
                if not destination:
                    raise SourceUnavailable("Magneto devolvió una redirección incompleta.")
                target = urljoin(current_url, destination)
                try:
                    current_url = validate_magneto_vacancy_url(target) if detail else self._validate_search_url(target)
                except ValueError:
                    raise SourceUnavailable("Magneto redireccionó a una ruta o destino no admitido.") from None
                continue
            if response.status_code >= 400:
                error = SourceUnavailable(f"Magneto respondió HTTP {response.status_code}.")
                error.http_status = response.status_code
                raise error
            return response, current_url
        raise SourceUnavailable("Magneto devolvió demasiadas redirecciones.")

    @staticmethod
    def _validate_search_url(url):
        parsed = urlparse((url or "").strip())
        if parsed.scheme.lower() != "https" or parsed.username or parsed.password or parsed.port not in (None, 443):
            raise ValueError("La URL de búsqueda de Magneto debe usar HTTPS.")
        if (parsed.hostname or "").lower() not in MAGNETO_HOSTS:
            raise ValueError("La URL de búsqueda no pertenece a Magneto Colombia.")
        if not re.fullmatch(r"/co/trabajos/buscar/[^?#]+", parsed.path, re.IGNORECASE):
            raise ValueError("La URL no corresponde a una búsqueda pública de Magneto.")
        return urlunparse(("https", (parsed.hostname or "").lower(), parsed.path.rstrip("/"), "", parsed.query, ""))

    @staticmethod
    def _assert_public_host(url):
        host = urlparse(url).hostname or ""
        try:
            addresses = {result[4][0] for result in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)}
            if not addresses or any(not ipaddress.ip_address(address).is_global for address in addresses):
                raise ValueError
        except (OSError, ValueError):
            raise SourceUnavailable("El host de Magneto no resuelve a una dirección pública.") from None

    @staticmethod
    def _clean(value):
        return " ".join(str(value or "").split()).strip(" ,;") or None

    @staticmethod
    def _walk_json_ld(value):
        if isinstance(value, list):
            for item in value:
                yield from MagnetoConnector._walk_json_ld(item)
        elif isinstance(value, dict):
            yield value
            graph = value.get("@graph")
            if graph is not None:
                yield from MagnetoConnector._walk_json_ld(graph)

    @classmethod
    def _job_posting(cls, soup):
        for script in soup.select('script[type="application/ld+json"]'):
            try:
                payload = json.loads(script.string or script.get_text())
            except (json.JSONDecodeError, TypeError):
                continue
            for item in cls._walk_json_ld(payload):
                types = item.get("@type", [])
                if isinstance(types, str):
                    types = [types]
                if any(str(value).casefold() == "jobposting" for value in types):
                    return item
        return {}

    @staticmethod
    def _is_salary(value):
        return bool(re.search(r"\$|salario|a convenir|COP", value or "", re.IGNORECASE))

    @staticmethod
    def _is_contract(value):
        return bool(re.search(
            r"t[eé]rmino (?:fijo|indefinido)|obra y labor|obra o labor|aprendizaje|prestaci[oó]n de servicios|temporal",
            value or "", re.IGNORECASE,
        ))

    @classmethod
    def parse(cls, html: str, base_url: str) -> list[JobListing]:
        """Extract cards; malformed or non-vacancy links are skipped."""
        soup = BeautifulSoup(html or "", "html.parser")
        found = {}
        for card in soup.select('article[class*="mg_job_card_"]'):
            anchor = card.select_one('h2 a[href]') or card.select_one('a[href*="/co/empleos/"]')
            title = cls._clean(anchor.get_text(" ", strip=True) if anchor else None)
            if not anchor or not title:
                continue
            try:
                url = validate_magneto_vacancy_url(urljoin(base_url, anchor.get("href", "")))
            except ValueError:
                continue

            company_node = card.select_one("h3") or card.select_one('[data-testid*="company"]')
            company_label = cls._clean(company_node.get_text(" ", strip=True) if company_node else None)
            company_parts = [cls._clean(part) for part in (company_label or "").split("|")]
            company = next((part for part in company_parts if part), None)
            contract_type = next((part for part in company_parts if part and cls._is_contract(part)), None)
            values = [cls._clean(node.get_text(" ", strip=True)) for node in card.select("p")]
            values = [value for value in values if value and value != title and value != company]
            salary = next((value for value in values if cls._is_salary(value)), None)
            contract_type = contract_type or next((value for value in values if cls._is_contract(value)), None)
            location = next((value for value in reversed(values) if value != salary and value != contract_type), None)
            published_node = card.select_one('[class*="published"]')
            raw_data = {}
            if published_node:
                publication = cls._clean(published_node.get_text(" ", strip=True))
                if publication and cls._normalize(publication) not in {
                    "fecha de publicacion no disponible", "no disponible", "sin fecha de publicacion",
                }:
                    raw_data["publication_label"] = publication
            listing = JobListing(
                source=cls.source,
                # The shared sample has a URL/identity conflict, so do not infer
                # an external ID from a slug or aria-label.
                external_id="",
                title=title,
                company=company,
                location=location,
                description=None,
                original_url=url,
                raw_data=raw_data,
                salary=salary,
                contract_type=contract_type,
            )
            found.setdefault(url, listing)
        return list(found.values())

    @classmethod
    def parse_detail(cls, html: str, base_url: str | None = None) -> dict:
        """Read JobPosting evidence and visible detail sections separately."""
        soup = BeautifulSoup(html or "", "html.parser")
        structured = cls._job_posting(soup)
        canonical_node = soup.select_one('link[rel="canonical"][href]')
        canonical = None
        canonical_invalid = False
        if canonical_node:
            try:
                canonical = validate_magneto_vacancy_url(urljoin(base_url or "https://www.magneto365.com", canonical_node["href"]))
            except ValueError:
                canonical_invalid = True

        visible = BeautifulSoup(str(soup), "html.parser")
        for element in visible.select("script, style, noscript, nav, header, footer"):
            element.decompose()
        main = visible.select_one("main") or visible.select_one("article") or visible.body or visible
        title_node = visible.select_one("h1")
        title = cls._clean(structured.get("title")) or cls._clean(title_node.get_text(" ", strip=True) if title_node else None)
        organization = structured.get("hiringOrganization") or {}
        company = cls._clean(organization.get("name")) if isinstance(organization, dict) else None

        locations = []
        raw_locations = structured.get("jobLocation") or []
        if not isinstance(raw_locations, list):
            raw_locations = [raw_locations]
        for place in raw_locations:
            address = place.get("address", {}) if isinstance(place, dict) else {}
            if isinstance(address, dict):
                locality = cls._clean(address.get("addressLocality"))
                region = cls._clean(address.get("addressRegion"))
                value = " · ".join(item for item in (locality, region) if item)
                if value and value not in locations:
                    locations.append(value)

        visible_text = main.get_text("\n", strip=True)
        labeled = cls._labeled_sections(main)
        description = cls._clean(structured.get("description"))
        if description:
            description = BeautifulSoup(description, "html.parser").get_text("\n", strip=True)
        elif visible_text:
            description = visible_text

        salary_obj = structured.get("baseSalary") or {}
        amount = salary_obj.get("value", {}) if isinstance(salary_obj, dict) else {}
        structured_salary = {}
        if isinstance(amount, dict):
            minimum = amount.get("minValue")
            maximum = amount.get("maxValue")
            if minimum not in (None, ""):
                structured_salary["min"] = minimum
            if maximum not in (None, "", 0, "0"):
                structured_salary["max"] = maximum
        elif amount not in (None, ""):
            structured_salary["value"] = amount
        if isinstance(salary_obj, dict) and salary_obj.get("currency"):
            structured_salary["currency"] = salary_obj["currency"]

        salary_values = []
        for value in labeled.get("salario", []):
            if cls._is_salary(value):
                salary_values.append({"source": "visible", "value": value})
        if structured_salary:
            salary_values.append({"source": "jobposting", "value": structured_salary})

        return {
            "title": title,
            "company": company,
            "external_id": cls._clean(
                str((structured.get("identifier") or {}).get("value"))
                if isinstance(structured.get("identifier"), dict) else structured.get("identifier")
            ),
            "canonical_url": canonical,
            "canonical_url_invalid": canonical_invalid,
            "locations": locations,
            "contract_type": cls._first_matching(labeled, "tipo de contrato"),
            "employment_type": structured.get("employmentType"),
            "salary_observations": salary_values,
            "requirements": cls._section_values(labeled, ("requisito", "conocimiento", "habilidad", "experiencia", "formacion")),
            "responsibilities": cls._section_values(labeled, ("responsabilidad", "funcion")),
            "description": description,
            "date_posted": structured.get("datePosted"),
        }

    @classmethod
    def _labeled_sections(cls, root):
        """Collect visible paragraphs under headings without relying on CSS hashes."""
        sections = {}
        for section in root.select("section"):
            heading = section.find(["h1", "h2", "h3", "h4", "h5", "h6"])
            if not heading:
                continue
            key = cls._normalize(heading.get_text(" ", strip=True))
            values = [cls._clean(node.get_text(" ", strip=True)) for node in section.select("p, li")]
            values = [value for value in values if value]
            if values:
                sections.setdefault(key, []).extend(values)
        return sections

    @classmethod
    def _first_matching(cls, sections, label):
        normalized = cls._normalize(label)
        return next((values[0] for key, values in sections.items() if normalized in key), None)

    @staticmethod
    def _section_values(sections, prefixes):
        return [
            value
            for key, values in sections.items()
            if any(prefix in key for prefix in prefixes)
            for value in values
        ]

    @classmethod
    def merge_details(cls, listing: JobListing, details: dict) -> tuple[JobListing, bool]:
        """Merge non-conflicting detail fields; return false for ambiguous identity."""
        from dataclasses import replace

        canonical = details.get("canonical_url")
        title = details.get("title")
        company = details.get("company")
        identity_conflict = bool(
            details.get("canonical_url_invalid")
            or (canonical and canonical != listing.original_url)
            or (title and cls._normalize(title) != cls._normalize(listing.title))
            or (company and listing.company and cls._normalize(company) != cls._normalize(listing.company))
            or (details.get("external_id") and listing.external_id and details["external_id"] != listing.external_id)
        )
        raw_data = dict(listing.raw_data or {})
        raw_data["details"] = details
        raw_data["details_fetch"] = {
            "status": "identity_ambiguous" if identity_conflict else "confirmed",
            "requested_url": listing.original_url,
        }
        if identity_conflict:
            return replace(listing, raw_data=raw_data), False

        if listing.salary and details.get("salary_observations"):
            raw_data["details"]["list_salary"] = listing.salary
        locations = details.get("locations") or []
        location = listing.location
        if not location and len(locations) == 1:
            location = locations[0]
        return replace(
            listing,
            location=location,
            description=listing.description or details.get("description"),
            salary=listing.salary or next(
                (observation["value"] for observation in details.get("salary_observations", [])
                 if observation.get("source") == "visible" and isinstance(observation.get("value"), str)),
                None,
            ),
            contract_type=listing.contract_type or details.get("contract_type"),
            raw_data=raw_data,
        ), True

    @staticmethod
    def _normalize(value):
        value = str(value or "").casefold().translate(str.maketrans("áéíóúüñ", "aeiouun"))
        return " ".join(re.sub(r"[^a-z0-9]+", " ", value).split())
