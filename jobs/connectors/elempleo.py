import json
import ipaddress
import re
import socket
import time
from dataclasses import replace
from datetime import timedelta
from urllib.parse import urlencode, urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .base import JobListing, SourceUnavailable
from jobs.identity import vacancy_dedupe_key
from profiles.locations import BOGOTA_AREA, MEDELLIN_AREA


ELEMPLEO_HOSTS = {"www.elempleo.com", "elempleo.com"}
ELEMPLEO_VACANCY_PATH = re.compile(r"^/co/ofertas-trabajo/[^/?#]+/?$", re.IGNORECASE)


def validate_elempleo_vacancy_url(url: str) -> str:
    """Validate and canonicalize a public Elempleo vacancy detail URL."""
    parsed = urlparse((url or "").strip())
    if parsed.scheme.lower() != "https":
        raise ValueError("La URL debe usar HTTPS.")
    if parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError("La URL no corresponde a una ficha pública admitida.")
    if (parsed.hostname or "").lower() not in ELEMPLEO_HOSTS:
        raise ValueError("Por ahora solo se admiten vacantes públicas de El Empleo.")
    if not ELEMPLEO_VACANCY_PATH.fullmatch(parsed.path):
        raise ValueError("Pega el enlace de una ficha de vacante de El Empleo.")
    host = (parsed.hostname or "").lower()
    return urlunparse(("https", host, parsed.path.rstrip("/"), "", "", ""))


def resolve_vacancy_url_provider(url: str):
    """Resolve a supported public vacancy URL to its source connector."""
    validate_elempleo_vacancy_url(url)
    return ElempleoConnector()


class ElempleoConnector:
    source = "elempleo_co"
    listing_path = re.compile(r"/co/ofertas-trabajo/[^/?#]+", re.IGNORECASE)

    def __init__(self, listing_url=None, session=None):
        self.listing_url = (listing_url or settings.ELEMPLEO_SEARCH_URL).rstrip("/")
        self.session = session or requests.Session()
        self.request_delay_seconds = 0.5
        self.detail_timeout = (5, 20)
        self.status_message = ""

    def fetch_vacancy_url(self, url: str) -> JobListing:
        """Fetch one public detail page, validating every host and redirect."""
        current_url = validate_elempleo_vacancy_url(url)
        response = None
        for _ in range(4):
            self._assert_public_host(current_url)
            response = self.session.get(
                current_url,
                headers={"User-Agent": "RamperJob/0.1 (public vacancy indexer)"},
                timeout=self.detail_timeout,
                allow_redirects=False,
            )
            if response.status_code not in {301, 302, 303, 307, 308}:
                break
            location = response.headers.get("Location")
            if not location:
                raise SourceUnavailable("El Empleo devolvió una redirección incompleta.")
            current_url = validate_elempleo_vacancy_url(urljoin(current_url, location))
        else:
            raise SourceUnavailable("La ficha de El Empleo tiene demasiadas redirecciones.")

        if response is None or response.status_code >= 400:
            status = response.status_code if response is not None else "desconocido"
            if status in {401, 403, 429}:
                raise SourceUnavailable("El Empleo no permite consultar esta ficha pública en este momento.")
            raise SourceUnavailable("No fue posible consultar la ficha pública de El Empleo.")
        if response.status_code in {301, 302, 303, 307, 308}:
            raise SourceUnavailable("La ficha de El Empleo tiene demasiadas redirecciones.")
        details = self.parse_detail(response.text, current_url)
        title = details.get("title")
        if not title:
            raise SourceUnavailable("La ficha no contiene un título de vacante interpretable.")
        raw_data = {"details": {key: value for key, value in details.items() if key not in {"title", "company"}}}
        return JobListing(
            source=self.source,
            external_id=details.get("external_id") or "",
            title=title,
            company=details.get("company"),
            location=details.get("city") or details.get("address"),
            description=details.get("description"),
            original_url=current_url,
            raw_data=raw_data,
            salary=details.get("salary_text"),
            contract_type=details.get("contract_type"),
        )

    @staticmethod
    def _assert_public_host(url: str) -> None:
        host = urlparse(url).hostname or ""
        try:
            addresses = {result[4][0] for result in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)}
            if not addresses or any(not ipaddress.ip_address(address).is_global for address in addresses):
                raise ValueError
        except (OSError, ValueError):
            raise SourceUnavailable("El host de la ficha no resuelve a una dirección pública.") from None

    def search_url(self, keyword: str, location: str | None = None, *, recent=True) -> str:
        slug = slugify(keyword)
        if not slug:
            raise ValueError("La palabra clave no produce una búsqueda válida.")
        city_slug = slugify(location) if location else ""
        city_path = f"/{city_slug}" if city_slug else ""
        url = f"{self.listing_url}{city_path}/trabajo-{slug}"
        return f"{url}?{urlencode({'PublishDate': 'hoy'})}" if recent else url

    def fetch(self, keywords: list[str], locations: list[str] | None = None, *, remote_ok=False) -> list[JobListing]:
        unique_keywords = list(dict.fromkeys(" ".join(term.split()) for term in keywords if term.strip()))
        if not unique_keywords:
            self.status_message = "El perfil no tiene palabras clave para consultar."
            return []

        unique_locations = list(dict.fromkeys(" ".join(location.split()) for location in locations or [] if location.strip()))
        if remote_ok or not unique_locations:
            unique_locations.insert(0, "")
        queries = [(keyword, location or None) for keyword in unique_keywords for location in unique_locations]
        listings_by_identity = {}
        query_errors = []
        successful_queries = 0
        for index, (keyword, location) in enumerate(queries):
            if index:
                time.sleep(self.request_delay_seconds)
            search_url = self.search_url(keyword, location, recent=True)
            try:
                response = self.session.get(
                    search_url,
                    headers={"User-Agent": "RamperJob/0.1 (public vacancy indexer)"},
                    timeout=(5, 20),
                )
            except requests.RequestException:
                query_errors.append(f"No se pudo consultar el término «{keyword}».")
                continue
            if response.status_code in {401, 403, 429}:
                raise SourceUnavailable("Elempleo no permite continuar la consulta pública.")
            if response.status_code >= 400:
                query_errors.append(f"Elempleo respondió HTTP {response.status_code} para «{keyword}».")
                continue

            successful_queries += 1
            page_url = response.url or search_url
            for listing in self.parse(response.text, base_url=page_url):
                identity = vacancy_dedupe_key(
                    listing.source, listing.external_id, listing.title, listing.company,
                    listing.location, listing.original_url,
                )
                if self._within_recent_window(listing):
                    listings_by_identity.setdefault(identity, listing)

        if successful_queries == 0:
            detail = query_errors[0] if query_errors else "No fue posible consultar las búsquedas públicas."
            raise SourceUnavailable(detail)
        listings = list(listings_by_identity.values())
        detail_errors = []
        for index, listing in enumerate(listings):
            time.sleep(self.request_delay_seconds)
            try:
                response = self.session.get(
                    listing.original_url,
                    headers={"User-Agent": "RamperJob/0.1 (public vacancy indexer)"},
                    timeout=self.detail_timeout,
                )
            except requests.RequestException:
                detail_errors.append(f"No se pudo consultar la ficha de «{listing.title}».")
                continue
            if response.status_code in {401, 403, 429}:
                detail_errors.append(f"Elempleo no permitió consultar la ficha de «{listing.title}».")
                continue
            if response.status_code >= 400:
                detail_errors.append(f"La ficha de «{listing.title}» respondió HTTP {response.status_code}.")
                continue
            try:
                enriched = self.parse_detail(response.text, response.url or listing.original_url)
            except (ValueError, TypeError, AttributeError):
                detail_errors.append(f"No se pudo interpretar la ficha de «{listing.title}».")
                continue
            listings[index] = self._merge_listing_details(listing, enriched)

        self.status_message = " ".join([*query_errors, *detail_errors])[:300]
        return listings

    def parse_detail(self, html: str, base_url: str | None = None) -> dict:
        """Extract the public fields shown on a single Elempleo vacancy page."""
        soup = BeautifulSoup(html, "html.parser")
        structured = {}
        for script in soup.select('script[type="application/ld+json"]'):
            try:
                data = json.loads(script.string or script.get_text())
            except (json.JSONDecodeError, TypeError):
                continue
            for item in self._walk_json_ld(data):
                if "jobposting" in str(item.get("@type", "")).lower():
                    structured = item
                    break
            if structured:
                break

        for element in soup.select("script, style, noscript, nav, header, footer"):
            element.decompose()
        visible_text = soup.get_text("\n", strip=True)
        labels = self._labeled_values(visible_text)
        visible_facts = self._visible_detail_facts(soup)
        quick_city = soup.select_one(".js-joboffer-city")
        quick_salary = soup.select_one(".js-joboffer-salary")
        place = (quick_city.get_text(" ", strip=True) if quick_city else None) or self._first_label(
            labels, "lugar", "ubicacion", "ubicacion del empleo"
        )
        salary_text = (quick_salary.get_text(" ", strip=True) if quick_salary else None) or self._first_label(
            labels, "salario", "salario ofrecido", "rango salarial"
        )
        contract = self._contract_type(
            visible_facts.get("tipo de contrato") or self._first_label(labels, "tipo de contrato", "contrato")
        )
        modality = visible_facts.get("modalidad") or self._first_label(labels, "modalidad", "modalidad de trabajo")
        if not modality and place:
            modality = self._find_modality(place)
        city, address = self._split_place(place)

        description_container = soup.select_one(".description-block")
        if description_container:
            for heading in description_container.select("h1, h2, h3, h4, h5, h6"):
                heading.decompose()
            description = description_container.get_text("\n", strip=True)
        else:
            description_html = structured.get("description")
            if description_html:
                description = BeautifulSoup(str(description_html), "html.parser").get_text("\n", strip=True)
            else:
                main = soup.select_one("main") or soup.select_one("article") or soup.body or soup
                description = main.get_text("\n", strip=True)

        salary_obj = structured.get("baseSalary") or {}
        if isinstance(salary_obj, dict):
            salary_value = salary_obj.get("value") or {}
            if isinstance(salary_value, dict):
                structured_salary = self._join_values((salary_value.get("minValue"), salary_value.get("maxValue")))
                salary_text = salary_text or structured_salary or str(salary_value.get("value") or "")
            salary_period = salary_obj.get("unitText") or (salary_value.get("unitText") if isinstance(salary_value, dict) else None)
        else:
            salary_period = None

        job_location = structured.get("jobLocation") or {}
        if isinstance(job_location, list):
            job_location = job_location[0] if job_location else {}
        address_obj = job_location.get("address", {}) if isinstance(job_location, dict) else {}
        if isinstance(address_obj, dict):
            structured_city = address_obj.get("addressLocality")
            city = city or structured_city
            address = address or self._clean_value(address_obj.get("streetAddress"))
            region = self._clean_value(address_obj.get("addressRegion"))
            if not city and region:
                city = region

        employment_type = structured.get("employmentType")
        schedule = visible_facts.get("jornada laboral") or self._first_label(labels, "horario", "jornada")
        if not schedule and isinstance(employment_type, str):
            schedule = {
                "FULL_TIME": "Tiempo completo",
                "PART_TIME": "Medio tiempo",
                "CONTRACTOR": "Por contrato",
                "TEMPORARY": "Temporal",
            }.get(employment_type.upper())
        if schedule and self._normalize_label(schedule) in {"mensual", "mensuales", "month"}:
            schedule = None

        h1 = soup.select_one("h1")
        og_title = soup.select_one('meta[property="og:title"]')
        return {
            "version": 1,
            "title": self._clean_value(structured.get("title"))
            or self._clean_value(h1.get_text(" ", strip=True) if h1 else None)
            or self._clean_value(og_title.get("content") if og_title else None),
            "company": self._clean_value(
                (structured.get("hiringOrganization") or {}).get("name")
                if isinstance(structured.get("hiringOrganization"), dict) else None
            ),
            "external_id": self._clean_value(
                str((structured.get("identifier") or {}).get("value"))
                if isinstance(structured.get("identifier"), dict)
                else str(structured.get("identifier")) if structured.get("identifier") else None
            ) or self._external_id_from_url(base_url),
            "salary_text": (salary_text or "").strip() or None,
            "salary_periodicity": (salary_period or self._salary_period(salary_text)).strip() if (salary_period or self._salary_period(salary_text)) else None,
            "city": self._clean_value(city),
            "address": self._clean_value(address),
            "modality": self._clean_value(modality or self._find_modality(description)),
            "contract_type": self._clean_value(contract),
            "education": visible_facts.get("nivel educativo") or self._first_label(labels, "nivel educativo", "nivel de estudios", "formacion") or None,
            "experience": visible_facts.get("experiencia minima") or self._first_label(labels, "experiencia", "experiencia requerida", "experiencia minima") or None,
            "area": visible_facts.get("area laboral") or self._first_label(labels, "area", "area de trabajo", "area laboral") or None,
            "schedule": self._clean_value(schedule),
            "responsibilities": self._section_values(labels, "responsabilidades", "funciones"),
            "requirements": self._section_values(
                labels, "requisitos", "habilidades", "habilidades blandas", "conocimientos",
                "conocimientos tecnicos", "deseables"
            ),
            "vacancy_count": visible_facts.get("numero de vacantes") or self._first_label(labels, "numero de vacantes", "vacantes") or None,
            "description": description or None,
            "employment_type": employment_type,
            "date_posted": structured.get("datePosted"),
        }

    @classmethod
    def _visible_detail_facts(cls, soup):
        """Read labeled value cards from Elempleo's visible vacancy detail panel."""
        facts = {}
        wanted = {
            "tipo de contrato", "experiencia minima", "area laboral", "jornada laboral",
            "nivel educativo", "numero de vacantes",
        }
        for label in soup.select("span"):
            normalized_label = cls._normalize_label(label.get_text(" ", strip=True))
            if normalized_label not in wanted:
                continue
            parent = label.parent
            value = next(
                (sibling.get_text(" ", strip=True) for sibling in parent.find_all("span", recursive=False) if sibling is not label),
                "",
            )
            if normalized_label == "numero de vacantes":
                value = re.sub(r"\s*vacantes?\s*$", "", value, flags=re.IGNORECASE).strip()
            if value:
                facts[normalized_label] = value
        return facts

    @staticmethod
    def _external_id_from_url(url):
        match = re.search(r"-(\d+)$", urlparse(url or "").path.rstrip("/"))
        return match.group(1) if match else None

    @staticmethod
    def _merge_listing_details(listing: JobListing, details: dict) -> JobListing:
        raw_data = dict(listing.raw_data or {})
        previous_details = raw_data.get("details") or {}
        merged_details = {
            **previous_details,
            **{
                key: value for key, value in details.items()
                if key != "description" and value not in (None, "", [])
            },
        }
        if listing.salary:
            merged_details.setdefault("list_salary", listing.salary)
        raw_data["details"] = merged_details
        actual_city = details.get("city")
        location = actual_city or listing.location
        if actual_city and details.get("address"):
            location = f"{actual_city} · {details['address']}"
        return replace(
            listing,
            location=location,
            description=details.get("description") or listing.description,
            salary=details.get("salary_text") or listing.salary,
            contract_type=details.get("contract_type") or listing.contract_type,
            raw_data=raw_data,
        )

    @staticmethod
    def _labeled_values(text):
        normalized = []
        for line in text.splitlines():
            line = " ".join(line.split())
            if not line:
                continue
            match = re.match(r"([^:]{2,60})\s*:\s*(.*)$", line)
            if match:
                normalized.append((ElempleoConnector._normalize_label(match.group(1)), match.group(2).strip()))
            else:
                suffix = re.match(
                    r"(.+?)\s+(nivel educativo|nivel laboral|experiencia m[ií]nima(?: requerida)?|"
                    r"[aá]rea laboral|tipo de contrato|n[uú]mero de vacantes)$",
                    line,
                    re.IGNORECASE,
                )
                if suffix:
                    label = ElempleoConnector._normalize_label(suffix.group(2))
                    value = suffix.group(1).strip()
                    if label == "numero de vacantes":
                        value = re.sub(r"\s+vacantes?$", "", value, flags=re.IGNORECASE)
                    if label.startswith("experiencia"):
                        value = re.sub(r"\s+de experiencia$", "", value, flags=re.IGNORECASE)
                    normalized.append((label, value))
                else:
                    heading = ElempleoConnector._normalize_label(line)
                    if heading in {
                        "responsabilidades", "funciones", "requisitos", "conocimientos tecnicos",
                        "conocimientos", "habilidades", "habilidades blandas", "deseables", "condiciones",
                    }:
                        normalized.append(("responsabilidades" if heading == "funciones" else heading, ""))
                    else:
                        normalized.append(("", line))
        return normalized

    @staticmethod
    def _normalize_label(value):
        value = value.casefold().translate(str.maketrans("áéíóúüñ", "aeiouun"))
        return " ".join(re.sub(r"[^a-z0-9]+", " ", value).split())

    @staticmethod
    def _first_label(labels, *wanted):
        wanted = {ElempleoConnector._normalize_label(item) for item in wanted}
        for label, value in labels:
            if label in wanted and value:
                return value
        return None

    @staticmethod
    def _section_values(labels, *wanted):
        wanted = {ElempleoConnector._normalize_label(item) for item in wanted}
        section_headings = {
            "responsabilidades", "funciones", "requisitos", "conocimientos tecnicos", "conocimientos",
            "habilidades", "habilidades blandas", "deseables", "condiciones", "descripcion del cargo",
        }
        collecting = False
        values = []
        for label, value in labels:
            if label in wanted:
                collecting = True
                if value:
                    values.append(value)
                continue
            if label in section_headings:
                collecting = False
            elif label and collecting:
                values.append(f"{label}: {value}" if value else label)
            elif collecting and value:
                values.append(value)
        return values

    @staticmethod
    def _find_modality(value):
        match = re.search(r"\b(presencial|remoto|h[ií]brid[oa]|teletrabajo)\b", value or "", re.IGNORECASE)
        return match.group(1).strip() if match else None

    @staticmethod
    def _split_place(value):
        if not value:
            return None, None
        text = " ".join(value.split())
        modality = ElempleoConnector._find_modality(text)
        if modality:
            text = re.sub(re.escape(modality), "", text, flags=re.IGNORECASE).strip(" ,;.-")
        cities = sorted(
            set((*BOGOTA_AREA, *MEDELLIN_AREA, "Cali", "Barranquilla", "Cartagena", "Bucaramanga",
                 "Manizales", "Pereira", "Armenia", "Cúcuta", "Ibagué", "Villavicencio", "Pasto",
                 "Montería", "Neiva", "Popayán", "Rionegro", "Bogotá D.C.")),
            key=len,
            reverse=True,
        )
        city_pattern = "|".join(re.escape(city) for city in cities)
        city_match = re.match(rf"({city_pattern})(?=\s|$|[,;])(.*)", text, re.IGNORECASE)
        if city_match:
            city, remainder = city_match.group(1).strip(), city_match.group(2).strip(" ,;.-")
            return city, remainder or None
        parts = re.split(r"[,;]", text, maxsplit=1)
        if len(parts) == 1:
            address_start = re.search(
                r"\b(?:av(?:enida)?\.?|calle|carrera|cra\.?|cl\.?|transversal|diagonal|autopista|km\.?|kil[oó]metro)\b",
                text,
                re.IGNORECASE,
            )
            if address_start:
                return text[:address_start.start()].strip() or None, text[address_start.start():].strip() or None
        return parts[0].strip() or None, parts[1].strip() or None if len(parts) > 1 else None

    @staticmethod
    def _salary_period(value):
        if not value:
            return None
        match = re.search(r"\b(mensual(?:es)?|quincenal(?:es)?|semanal(?:es)?|diari[oa]s?)\b", value, re.IGNORECASE)
        return match.group(1) if match else None

    @staticmethod
    def _salary_from_text(value):
        match = re.search(
            r"\$\s?[\d.,]+(?:\s*(?:a|-)\s*\$?\s?[\d.,]+)?\s*(?:millones?|mill[oó]n)?",
            value or "",
            re.IGNORECASE,
        )
        return " ".join(match.group(0).split()) if match else None

    @staticmethod
    def _json_ld_salary(value):
        if not isinstance(value, dict):
            return None
        amount = value.get("value") or {}
        if isinstance(amount, dict):
            lower, upper = amount.get("minValue"), amount.get("maxValue")
            unit = value.get("unitText") or amount.get("unitText")
            salary = f"{lower}–{upper}" if lower is not None and upper is not None else (
                amount.get("value") or lower or upper
            )
            return f"{salary} {unit}".strip() if salary is not None else None
        return str(amount) if amount else None

    @staticmethod
    def _clean_value(value):
        return " ".join(str(value).split()).strip(" ,;.-") if value else None

    @classmethod
    def _contract_type(cls, value):
        value = cls._clean_value(value)
        if value and value.upper() in {
            "CONTRACTOR", "FULL_TIME", "INTERNSHIP", "OTHER", "PART_TIME",
            "PER_DIEM", "TEMPORARY", "UNKNOWN", "VOLUNTEER",
        }:
            return None
        return value

    def parse(self, html: str, base_url: str | None = None) -> list[JobListing]:
        soup = BeautifulSoup(html, "html.parser")
        base_url = base_url or self.listing_url
        listings = self._from_json_ld(soup, base_url)
        if listings:
            return listings
        return self._from_job_links(soup, base_url)

    def _from_json_ld(self, soup: BeautifulSoup, base_url: str) -> list[JobListing]:
        found = []
        for script in soup.select('script[type="application/ld+json"]'):
            try:
                data = json.loads(script.string or script.get_text())
            except (json.JSONDecodeError, TypeError):
                continue
            for item in self._walk_json_ld(data):
                if "jobposting" not in str(item.get("@type", "")).lower():
                    continue
                url = urljoin(base_url, str(item.get("url", "")))
                if not url:
                    continue
                organization = item.get("hiringOrganization") or {}
                address = item.get("jobLocation") or {}
                if isinstance(address, list):
                    address = address[0] if address else {}
                address = address.get("address", {}) if isinstance(address, dict) else {}
                description = BeautifulSoup(str(item.get("description", "")), "html.parser").get_text("\n", strip=True)
                found.append(
                    JobListing(
                        source=self.source,
                        external_id=self._external_id(url),
                        title=str(item.get("title", "")).strip(),
                        company=organization.get("name") if isinstance(organization, dict) else None,
                        location=self._join_values(address.get(key) for key in ("addressLocality", "addressRegion")),
                        description=description or None,
                        original_url=url,
                        raw_data={"datePosted": item.get("datePosted"), "employmentType": item.get("employmentType")},
                        salary=self._json_ld_salary(item.get("baseSalary")),
                        contract_type=self._contract_type(item.get("employmentType")),
                    )
                )
        return self._dedupe(found)

    def _from_job_links(self, soup: BeautifulSoup, base_url: str) -> list[JobListing]:
        found = []
        for anchor in soup.select("a[href]"):
            url = urljoin(base_url, anchor.get("href", ""))
            if not self.listing_path.search(urlparse(url).path):
                continue
            title = anchor.get_text(" ", strip=True)
            title = re.sub(r"^Vacante:\s*", "", title, flags=re.IGNORECASE).strip()
            if not title:
                continue
            card = self._card_for(anchor)
            text = card.get_text("\n", strip=True) if card else title
            company = self._company_from_text(text)
            location = self._location_from_text(text)
            description = self._description_from_text(text, title, company, location)
            publication_label = self._publication_label(text)
            found.append(
                JobListing(
                    source=self.source,
                    external_id=self._external_id(url),
                    title=title,
                    company=company,
                    location=location,
                    description=description,
                    original_url=url,
                    raw_data={"publication_label": publication_label} if publication_label else {},
                    salary=self._salary_from_text(text),
                    contract_type=self._contract_type(
                        self._first_label(self._labeled_values(text), "tipo de contrato", "contrato")
                    ),
                )
            )
        return self._dedupe(found)

    @staticmethod
    def _walk_json_ld(data):
        if isinstance(data, dict):
            yield data
            graph = data.get("@graph", [])
            if isinstance(graph, list):
                yield from graph
        elif isinstance(data, list):
            for item in data:
                yield from ElempleoConnector._walk_json_ld(item)

    @staticmethod
    def _card_for(anchor):
        for parent in anchor.parents:
            if parent.name in {"article", "li"}:
                return parent
            if parent.name == "div" and parent.get("class") and len(parent.get_text(" ", strip=True)) < 7000:
                return parent
        return anchor.parent

    @staticmethod
    def _company_from_text(text):
        match = re.search(r"Trabaja en\s+([^\n]+)", text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    @staticmethod
    def _location_from_text(text):
        match = re.search(r"(?:Ubicación\s*)?\n([^\n]+)\n(?:Ubicación|Modalidad|Nivel laboral)", text, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            return value if value else None
        match = re.search(r"\b(Bogotá(?:\s+D\.?C\.?)?|Medellín|Cali|Barranquilla|Remoto)\b", text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    @staticmethod
    def _description_from_text(text, title, company, location):
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        remove = {title.casefold(), (company or "").casefold(), (location or "").casefold()}
        remaining = [line for line in lines if line.casefold() not in remove and not re.fullmatch(r"Publicado .+", line, re.IGNORECASE)]
        return "\n".join(remaining) or None

    @staticmethod
    def _external_id(url):
        tail = urlparse(url).path.rstrip("/").split("/")[-1]
        digits = re.search(r"(\d+)$", tail)
        return digits.group(1) if digits else tail

    @staticmethod
    def _publication_label(text):
        for line in text.splitlines():
            line = " ".join(line.split())
            if re.fullmatch(r"(?:Hoy|Ayer|Hace (?:\d+|más de 1) (?:día|días|semana|semanas|mes|meses))", line, re.IGNORECASE):
                return line
            match = re.search(r"Publicado\s+(hoy|ayer|hace\s+.+)$", line, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    @staticmethod
    def _within_recent_window(listing):
        published_at = parse_datetime(str(listing.raw_data.get("datePosted", "")))
        if published_at:
            if timezone.is_naive(published_at):
                published_at = timezone.make_aware(published_at, timezone.get_current_timezone())
            return published_at >= timezone.now() - timedelta(hours=24)

        label = str(listing.raw_data.get("publication_label", "")).casefold()
        if not label:
            return True
        if "hoy" in label or "ayer" in label or re.search(r"hace\s+1\s+d[ií]a", label):
            return True
        if re.search(r"hace\s+(?:\d+|más de 1)\s+(?:d[ií]as?|semanas?|meses?)", label):
            return False
        return True

    @staticmethod
    def _join_values(values):
        return ", ".join(str(value).strip() for value in values if value)

    @staticmethod
    def _dedupe(listings):
        unique = {}
        for listing in listings:
            key = vacancy_dedupe_key(
                listing.source, listing.external_id, listing.title, listing.company,
                listing.location, listing.original_url,
            )
            unique.setdefault(key, listing)
        return list(unique.values())
