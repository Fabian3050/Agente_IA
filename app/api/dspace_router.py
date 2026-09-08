from fastapi import APIRouter, Depends, Query, HTTPException
from app.services.dspace_service import DSpaceService

# Nota: El archivo se llama dscape_router.py, pero el router manejará 'dspace'
router = APIRouter(
    prefix="/dspace",
    tags=["DSpace Integration"]
)

# Dependencia de FastAPI para inyectar el servicio
def get_dspace_service():
    return DSpaceService()

@router.get("/items")
async def get_items(
    page: int = Query(0, description="Número de página (índice base 0)"),
    size: int = Query(20, description="Cantidad de registros de metadatos por página"),
    dspace_service: DSpaceService = Depends(get_dspace_service)
):
    """
    Obtiene la lista de publicaciones desde DSpace.
    Devuelve estrictamente los metadatos de los registros, no archivos adjuntos (PDFs).
    """
    try:
        return await dspace_service.get_all_items(page=page, size=size)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error comunicándose con DSpace: {str(e)}")

@router.get("/items/{item_id}")
async def get_item_metadata(
    item_id: str,
    dspace_service: DSpaceService = Depends(get_dspace_service)
):
    """
    Obtiene los metadatos completos de un registro individual en base a su UUID.
    """
    try:
        return await dspace_service.get_metadata(item_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo el ítem {item_id}: {str(e)}")

@router.get("/count-missing")
async def count_missing(
    dspace_service: DSpaceService = Depends(get_dspace_service)
):
    """
    Cuenta los items que no tienen abstract ni DOI y retorna sus UUIDs.
    """
    try:
        return await dspace_service.count_missing_metadata_optimized()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error contando items: {str(e)}")