import httpx
from typing import List, Optional
from models.metadata_model import MetadataResponse

UNPAYWALL_EMAIL = "agente_ia_vriic@usach.cl"


def _normalize_oa_status(raw_status: Optional[str]) -> Optional[str]:
    """Normaliza el estado OA a uno de los 5 valores estándar: Gold, Green, Bronze, Hybrid, Closed."""
    if not raw_status:
        return None
    s = raw_status.strip().capitalize()
    if s in ["Gold", "Green", "Bronze", "Hybrid", "Closed"]:
        return s
    return "Closed"


def _normalize_version_type(raw_version: Optional[str]) -> Optional[str]:
    """Normaliza la versión del manuscrito a: Preprint, Postprint o PublishedVersion."""
    if not raw_version:
        return None
    v = raw_version.lower()
    if "submitted" in v or "preprint" in v:
        return "Preprint"
    if "accepted" in v or "postprint" in v:
        return "Postprint"
    if "published" in v:
        return "PublishedVersion"
    return "PublishedVersion"


async def search_unpaywall(query: str, limit: int = 5) -> List[MetadataResponse]:
    # Unpaywall REST API se centra exclusivamente en consultas directas por DOI
    return []


async def get_by_doi_unpaywall(doi: str) -> Optional[dict]:
    clean_doi = doi.replace("https://doi.org/", "").strip()
    url = f"https://api.unpaywall.org/v2/{clean_doi}"
    params = {"email": UNPAYWALL_EMAIL}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[Unpaywall] Error consultando DOI {doi}: {e}")
            return None


async def get_metadata_by_doi_unpaywall(doi: str) -> Optional[MetadataResponse]:
    data = await get_by_doi_unpaywall(doi)
    if not data:
        return None

    clean_doi = doi.replace("https://doi.org/", "").strip()
    title = data.get("title") or "Sin título"
    oa_status = _normalize_oa_status(data.get("oa_status"))
    
    best_loc = data.get("best_oa_location") or {}
    license_val = best_loc.get("license")
    version_val = _normalize_version_type(best_loc.get("version"))
    
    return MetadataResponse(
        title=title,
        authors=[],
        doi=clean_doi,
        year=data.get("year"),
        source="unpaywall",
        url=data.get("doi_url"),
        oa_status=oa_status,
        license=license_val,
        version_type=version_val,
        derechos_acceso=oa_status
    )
