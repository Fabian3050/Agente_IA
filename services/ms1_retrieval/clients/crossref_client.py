import httpx
import re
from typing import List, Optional
from models.metadata_model import MetadataResponse

CROSSREF_POLITE_USER_AGENT = "DSpaceCRIS-Agent/3.0 (mailto:agente_ia_vriic@usach.cl)"


def clean_crossref_abstract(raw_abstract: Optional[str]) -> Optional[str]:
    """
    Elimina etiquetas XML/JATS (<jats:p>, <jats:italic>, <jats:title>, etc.)
    del abstract proveniente de Crossref según la Sección 3.4.
    """
    if not raw_abstract:
        return None
    # Eliminar cualquier etiqueta xml / jats
    cleaned = re.sub(r"<[^>]+>", " ", str(raw_abstract))
    # Limpiar espacios repetidos y saltos
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned if cleaned else None


def _parse_crossref_item(item: dict) -> MetadataResponse:
    title = item.get("title", [""])[0] if item.get("title") else "No title"
    authors = []
    for author in item.get("author", []):
        name = f"{author.get('given', '')} {author.get('family', '')}".strip()
        if name:
            authors.append(name)
    
    doi = item.get("DOI")
    
    year = None
    published = item.get("published-print") or item.get("published-online")
    if published and published.get("date-parts"):
        year = published["date-parts"][0][0]
    
    item_url = item.get("URL")
    abstract = clean_crossref_abstract(item.get("abstract"))
    
    funding_sources = []
    funding_agency = None
    funding_id = None
    funding_grant_number = None

    funders = item.get("funder", [])
    if funders:
        primary_funder = funders[0]
        funding_agency = primary_funder.get("name")
        funding_id = primary_funder.get("DOI")  # Funder ID persistente en Crossref
        awards = primary_funder.get("award", [])
        if awards:
            funding_grant_number = str(awards[0])

        for funder in funders:
            if funder.get("name"):
                funding_sources.append(funder.get("name"))

    funding_sources = list(dict.fromkeys(funding_sources)) if funding_sources else None
    keywords = item.get("subject", []) if item.get("subject") else None

    # Licencia
    license_url = None
    licenses = item.get("license", [])
    if licenses and licenses[0].get("URL"):
        license_url = licenses[0].get("URL")

    return MetadataResponse(
        title=title,
        authors=authors,
        doi=doi,
        year=year,
        source="crossref",
        url=item_url,
        abstract=abstract,
        funding_source=funding_sources,
        funding_agency=funding_agency,
        funding_id=funding_id,
        funding_grant_number=funding_grant_number,
        license=license_url,
        keywords=keywords,
        author_keywords=keywords
    )


async def search_crossref(query: str, limit: int = 5) -> List[MetadataResponse]:
    url = "https://api.crossref.org/works"
    params = {"query": query, "rows": limit}
    headers = {"User-Agent": CROSSREF_POLITE_USER_AGENT}
    results = []
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, headers=headers, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            items = data.get("message", {}).get("items", [])
            for item in items:
                results.append(_parse_crossref_item(item))
        except Exception as e:
            print(f"[Crossref] Error buscando por query '{query}': {e}")
            
    return results


async def get_by_doi_crossref(doi: str) -> Optional[MetadataResponse]:
    clean_doi = doi.replace("https://doi.org/", "").strip()
    url = f"https://api.crossref.org/works/{clean_doi}"
    headers = {"User-Agent": CROSSREF_POLITE_USER_AGENT}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=10.0)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()
            item = data.get("message", {})
            return _parse_crossref_item(item)
        except Exception as e:
            print(f"[Crossref] Error consultando DOI '{doi}': {e}")
            
    return None


async def get_doi_by_title_and_abstract_crossref(title: Optional[str] = None, abstract: Optional[str] = None) -> Optional[str]:
    if not title and not abstract:
        return None
    
    parts = []
    if title:
        parts.append(title)
    if abstract:
        parts.append(abstract)
        
    query = " ".join(parts)
    url = "https://api.crossref.org/works"
    params = {"query": query, "rows": 1}
    headers = {"User-Agent": CROSSREF_POLITE_USER_AGENT}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, headers=headers, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            items = data.get("message", {}).get("items", [])
            if items:
                return items[0].get("DOI")
        except Exception as e:
            print(f"[Crossref] Error buscando DOI por título: {e}")
    return None
