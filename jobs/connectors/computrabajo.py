import ipaddress
import re
import socket
import time
from dataclasses import replace
from urllib.parse import urlencode, urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.utils.text import slugify

from jobs.identity import vacancy_dedupe_key

from .base import JobListing, SourcePartiallyUnavailable, SourceUnavailable


COMPUTRABAJO_HOSTS = {"co.computrabajo.com", "www.computrabajo.com.co"}
REDIRECT_STATUSES = {301, 302, 303, 307, 308}
BLOCK_STATUSES = {401, 403, 429}


def validate_computrabajo_url(url, *, detail=False):
    """Validate and canonicalize a public Colombian search or vacancy URL."""
    parsed = urlparse((url or "").strip())
    if parsed.scheme.lower() != "https" or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError("La URL pública de Computrabajo no es válida.")
    if (parsed.hostname or "").lower() not in COMPUTRABAJO_HOSTS:
        raise ValueError("La URL no pertenece a Computrabajo Colombia.")
    if detail:
        if not re.fullmatch(r"/ofertas-de-trabajo/[^/?#]+/?", parsed.path, re.IGNORECASE):
            raise ValueError("La URL no corresponde a una ficha pública de Computrabajo.")
    elif not re.fullmatch(r"/trabajo-de-[^/?#]+(?:-en-[^/?#]+)?/?", parsed.path, re.IGNORECASE):
        raise ValueError("La URL no corresponde a una búsqueda pública de Computrabajo.")
    return urlunparse(("https", parsed.hostname.lower(), parsed.path.rstrip("/"), "", parsed.query, ""))


class ComputrabajoConnector:
    source = "computrabajo_co"
    listing_url = "https://co.computrabajo.com"

    def __init__(self, session=None):
        self.session = session or requests.Session()
        self.user_agent = settings.COMPUTRABAJO_USER_AGENT
        self.request_delay_seconds = 0.5
        self.request_timeout = (5, 20)
        self.max_redirects = 3
        self.status_message = ""

    def search_url(self, keyword, location=None):
        keyword_slug = slugify(" ".join((keyword or "").split()))
        if not keyword_slug:
            raise ValueError("La palabra clave no produce una búsqueda válida.")
        city_slug = slugify(" ".join(location.split())) if location else ""
        city_path = f"-en-{city_slug}" if city_slug else ""
        url = f"{self.listing_url}/trabajo-de-{keyword_slug}{city_path}"
        return f"{url}?{urlencode({'pubdate': '1', 'p': '1', 'by': 'relevance'})}"

    def fetch_titles(self, keywords, locations=None, *, remote_ok=False):
        """Fetch one page for each requested term and expanded location."""
        self.status_message = ""
        unique_keywords = list(dict.fromkeys(" ".join(term.split()) for term in keywords if term.strip()))
        if not unique_keywords:
            self.status_message = "El perfil no tiene palabras clave para consultar."
            return []
        unique_locations = list(dict.fromkeys(" ".join(value.split()) for value in locations or [] if value.strip()))
        if remote_ok or not unique_locations:
            unique_locations.insert(0, "")
        queries = [(keyword, location or None) for keyword in unique_keywords for location in unique_locations]
        listings_by_identity = {}
        query_errors = []
        succeeded = 0
        for index, (keyword, location) in enumerate(queries):
            if index:
                time.sleep(self.request_delay_seconds)
            search_url = self.search_url(keyword, location)
            try:
                response, final_url = self._get_public(search_url, detail=False)
            except SourceUnavailable as exc:
                if getattr(exc, "http_status", None) in BLOCK_STATUSES:
                    message = "Computrabajo no permite continuar la consulta pública."
                    self.status_message = message
                    partial_listings = list(listings_by_identity.values())
                    if partial_listings:
                        raise SourcePartiallyUnavailable(message, partial_listings) from None
                    raise SourceUnavailable(message) from None
                query_errors.append(f"No se pudo consultar «{keyword}» en Computrabajo.")
                continue
            except requests.RequestException:
                query_errors.append(f"No se pudo consultar «{keyword}» en Computrabajo.")
                continue
            succeeded += 1
            for listing in self.parse(response.text, final_url):
                identity = vacancy_dedupe_key(
                    listing.source, listing.external_id, listing.title, listing.company,
                    listing.location, listing.original_url,
                )
                listings_by_identity.setdefault(identity, listing)

        if not succeeded:
            raise SourceUnavailable(query_errors[0] if query_errors else "No fue posible consultar Computrabajo.")
        self.status_message = " ".join(query_errors)[:300]
        return list(listings_by_identity.values())

    def fetch_details(self, listings):
        """Fetch each unique detail once; retain cards and stop on source blocks."""
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
            listing = listings[index]
            try:
                response, final_url = self._get_public(url, detail=True)
            except SourceUnavailable as exc:
                if getattr(exc, "http_status", None) in BLOCK_STATUSES:
                    message = "Computrabajo bloqueó la consulta de fichas; se conservaron los datos del listado."
                    self.status_message = " ".join(filter(None, (self.status_message, message)))[:300]
                    raise SourcePartiallyUnavailable(self.status_message, listings) from None
                detail_errors.append(str(exc) or f"No se pudo consultar la ficha de «{listing.title}».")
                continue
            except requests.RequestException:
                detail_errors.append(f"No se pudo consultar la ficha de «{listing.title}».")
                continue
            try:
                details = self.parse_detail(response.text)
            except (ValueError, TypeError, AttributeError):
                detail_errors.append(f"No se pudo interpretar la ficha de «{listing.title}».")
                continue
            listings[index] = self._merge_details(listing, details, final_url)
        self.status_message = " ".join(filter(None, (self.status_message, *detail_errors)))[:300]
        return listings

    def fetch(self, keywords, locations=None, *, remote_ok=False):
        try:
            return self.fetch_details(self.fetch_titles(keywords, locations=locations, remote_ok=remote_ok))
        except SourcePartiallyUnavailable as exc:
            return exc.listings

    def _get_public(self, url, *, detail):
        current_url = validate_computrabajo_url(url, detail=detail)
        for redirect_count in range(self.max_redirects + 1):
            self._assert_public_host(current_url)
            response = self.session.get(
                current_url,
                headers={"User-Agent": self.user_agent},
                timeout=self.request_timeout,
                allow_redirects=False,
            )
            if response.status_code in BLOCK_STATUSES:
                error = SourceUnavailable("Computrabajo rechazó la consulta pública.")
                error.http_status = response.status_code
                raise error
            if response.status_code in REDIRECT_STATUSES:
                if redirect_count >= self.max_redirects:
                    raise SourceUnavailable("Computrabajo devolvió demasiadas redirecciones.")
                destination = response.headers.get("Location")
                if not destination:
                    raise SourceUnavailable("Computrabajo devolvió una redirección incompleta.")
                current_url = validate_computrabajo_url(urljoin(current_url, destination), detail=detail)
                continue
            if response.status_code >= 400:
                error = SourceUnavailable(f"Computrabajo respondió HTTP {response.status_code}.")
                error.http_status = response.status_code
                raise error
            return response, current_url
        raise SourceUnavailable("Computrabajo devolvió demasiadas redirecciones.")

    @staticmethod
    def _assert_public_host(url):
        host = urlparse(url).hostname or ""
        try:
            addresses = {result[4][0] for result in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)}
            if not addresses or any(not ipaddress.ip_address(address).is_global for address in addresses):
                raise ValueError
        except (OSError, ValueError):
            raise SourceUnavailable("El host de Computrabajo no resuelve a una dirección pública.") from None

    def parse(self, html, base_url):
        soup = BeautifulSoup(html or "", "html.parser")
        found = []
        for card in soup.select("article.box_offer"):
            anchor = card.select_one("a.js-o-link[href]")
            title = anchor.get_text(" ", strip=True) if anchor else ""
            if not anchor or not title:
                continue
            url = validate_computrabajo_url(urljoin(base_url, anchor.get("href", "")), detail=True)
            external_id = (card.get("data-id") or "").strip()
            company_node = card.select_one("[offer-grid-article-company-url]") or card.select_one("a[href*='empresa']")
            location_node = card.select_one("p.fs16.fc_base.mt5")
            salary_node = card.select_one("div.fs13.mt15 span.dIB.mr10")
            publication_node = card.select_one("p.fs13.fc_aux.mt15")
            description_node = card.select_one("[data-testid='offer-description'], .offer-description")
            raw_data = {}
            publication_label = " ".join(publication_node.get_text(" ", strip=True).split()) if publication_node else None
            if publication_label:
                raw_data["publication_label"] = publication_label
            if description_node:
                raw_data["listing_description"] = description_node.get_text("\n", strip=True)
            found.append(JobListing(
                source=self.source,
                external_id=external_id,
                title=" ".join(title.split()),
                company=" ".join(company_node.get_text(" ", strip=True).split()) if company_node else None,
                location=" ".join(location_node.get_text(" ", strip=True).split()) if location_node else None,
                description=description_node.get_text("\n", strip=True) if description_node else None,
                original_url=url,
                raw_data=raw_data,
                salary=" ".join(salary_node.get_text(" ", strip=True).split()) if salary_node else None,
            ))
        return self._dedupe(found)

    def parse_detail(self, html):
        soup = BeautifulSoup(html or "", "html.parser")
        title_node = soup.select_one("h1")
        description_node = soup.select_one("[data-testid='offer-description'], .fs16.t_word_wrap")
        text = soup.get_text("\n", strip=True)
        summary = "\n".join(soup.select_one("main").stripped_strings) if soup.select_one("main") else text
        salary = self._summary_value(summary, r"\$\s?[^\n]+")
        contract = self._summary_value(summary, r"Contrato\s+de\s+[^\n]+")
        modality = self._summary_value(summary, r"(Presencial|Remoto|H[ií]brido|Teletrabajo)")
        location = self._label_value(summary, "Ubicación")
        requirements = self._section_text(soup, ("Requisitos", "Requerimientos"))
        responsibilities = self._section_text(soup, ("Principales funciones", "Responsabilidades", "Funciones"))
        details = {
            "title": " ".join(title_node.get_text(" ", strip=True).split()) if title_node else None,
            "company": self._company_from_detail(soup),
            "description": description_node.get_text("\n", strip=True) if description_node else None,
            "salary": salary,
            "contract_type": contract,
            "location": location,
            "modality": modality,
            "requirements": requirements,
            "responsibilities": responsibilities,
        }
        return {key: value for key, value in details.items() if value}

    @staticmethod
    def _summary_value(text, pattern):
        match = re.search(pattern, text, re.IGNORECASE)
        return " ".join(match.group(0).split()) if match else None

    @staticmethod
    def _label_value(text, label):
        match = re.search(rf"{re.escape(label)}:\s*([^\n]+)", text, re.IGNORECASE)
        return " ".join(match.group(1).split()) if match else None

    @staticmethod
    def _company_from_detail(soup):
        node = soup.select_one("[data-testid*='company'], .box_company, .company_name")
        return " ".join(node.get_text(" ", strip=True).split()) if node else None

    @staticmethod
    def _section_text(soup, headings):
        wanted = {" ".join(item.casefold().split()) for item in headings}
        for heading in soup.select("h2, h3, h4, p"):
            if " ".join(heading.get_text(" ", strip=True).casefold().split()).rstrip(":") not in wanted:
                continue
            values = []
            for sibling in heading.find_all_next():
                if sibling.name in {"h2", "h3", "h4"}:
                    break
                if sibling.name in {"p", "li"}:
                    value = sibling.get_text(" ", strip=True)
                    if value:
                        values.append(value)
            if values:
                return values
        return []

    @staticmethod
    def _merge_details(listing, details, final_url):
        conflicts = {}
        for detail_key, listing_value in (("salary", listing.salary), ("location", listing.location), ("company", listing.company)):
            detail_value = details.get(detail_key)
            if detail_value and listing_value and detail_value.casefold() != listing_value.casefold():
                conflicts[f"listing_{detail_key}"] = listing_value
        raw_data = {**(listing.raw_data or {}), "details": details}
        if conflicts:
            raw_data["details"].update(conflicts)
        return replace(
            listing,
            title=details.get("title") or listing.title,
            company=details.get("company") or listing.company,
            location=details.get("location") or listing.location,
            description=details.get("description") or listing.description,
            original_url=final_url,
            raw_data=raw_data,
            salary=details.get("salary") or listing.salary,
            contract_type=details.get("contract_type") or listing.contract_type,
        )

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
