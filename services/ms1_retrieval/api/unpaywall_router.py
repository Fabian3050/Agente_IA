from fastapi import APIRouter, HTTPException
from typing import Optional, List
from clients.unpaywall_client import get_by_doi_unpaywall, search_unpaywall
from models.metadata_model import MetadataResponse

router = APIRouter(
    prefix="/unpaywall",
    tags=["Unpaywall OA"]
)

@router.get("/doi/{doi:path}")
async def get_unpaywall_by_doi(doi: str):
    """
    Recupera metadatos e información de Open Access a partir de un DOI utilizando Unpaywall.
    """
    result = await get_by_doi_unpaywall(doi)
    if not result:
        raise HTTPException(status_code=404, detail="DOI no encontrado en Unpaywall")
    return result

@router.get("/search", response_model=List[MetadataResponse])
async def search_unpaywall_meta(query: str, limit: int = 5):
    return await search_unpaywall(query, limit)

