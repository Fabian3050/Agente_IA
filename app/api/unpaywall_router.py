from fastapi import APIRouter, HTTPException
from typing import Optional, List
from app.clients.unpaywall_client import get_by_doi_unpaywall, search_unpaywall
from app.models.metadata_model import MetadataResponse

router = APIRouter(
    prefix="/unpaywall",
    tags=["Unpaywall"]
)

@router.get("/doi/{doi:path}")
async def get_metadata_by_doi(doi: str):
    """
    Recupera metadatos e información de Open Access a partir de un DOI utilizando Unpaywall.
    """
    result = await get_by_doi_unpaywall(doi)
    if not result:
        raise HTTPException(status_code=404, detail="DOI no encontrado en Unpaywall")
    return result

@router.get("/search", response_model=List[MetadataResponse])
async def search_metadata(query: str, limit: int = 5):
    """
    Búsqueda de metadatos en Unpaywall (Nota: Unpaywall se centra principalmente en búsqueda por DOI, esta función puede estar limitada).
    """
    return await search_unpaywall(query, limit)
