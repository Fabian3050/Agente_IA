from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Optional
from app.services.classification_service import ClassificationService
from app.models.classification_model import OCDEClassificationResponse, ODSClassificationResponse

router = APIRouter(prefix="/classify", tags=["classification"])

def get_classification_service():
    return ClassificationService()

@router.get("/doi/{doi:path}", response_model=OCDEClassificationResponse)
async def classify_by_doi(
    doi: str,
    source: Optional[str] = Query(None, description="Fuente específica (crossref, openalex, etc)"),
    svc: ClassificationService = Depends(get_classification_service)
):
    """
    Busca metadatos de un artículo por su DOI y utiliza Llama 3.2 para clasificarlo según el estándar OCDE.
    """
    try:
        return await svc.classify_article_by_doi(doi, source)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/ods/doi/{doi:path}", response_model=ODSClassificationResponse)
async def classify_by_ods(
    doi: str,
    source: Optional[str] = Query(None, description="Fuente específica (crossref, openalex, etc)"),
    svc: ClassificationService = Depends(get_classification_service)
):
    """
    Busca metadatos de un artículo por su DOI y utiliza Llama 3.2 para clasificarlo según los ODS (Objetivos de Desarrollo Sostenible).
    """
    try:
        return await svc.classify_article_by_ods(doi, source)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
