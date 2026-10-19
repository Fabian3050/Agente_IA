from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.services.dspace_service import DSpaceService
from app.database import get_db

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
    save_to_db: bool = Query(False, description="Guardar snapshot de métricas en histórico y poblar la cola de enriquecimiento en BD"),
    dspace_service: DSpaceService = Depends(get_dspace_service),
    db: Session = Depends(get_db)
):
    """
    Cuenta los items que no tienen abstract ni DOI dentro de valid_resource_types.
    Opcionalmente guarda el histórico de métricas y la cola de enriquecimiento en la base de datos.
    """
    try:
        return await dspace_service.count_missing_metadata_optimized(save_to_db=save_to_db, db=db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error contando items: {str(e)}")

@router.get("/metrics-history")
def get_metrics_history(
    limit: int = Query(30, description="Cantidad máxima de registros históricos a retornar"),
    db: Session = Depends(get_db)
):
    """
    Retorna el histórico cronológico de métricas del repositorio para alimentar dashboards.
    """
    from app.models.db_models import DSpaceMetricsHistory
    records = db.query(DSpaceMetricsHistory).order_by(DSpaceMetricsHistory.fecha.desc()).limit(limit).all()
    return records

@router.get("/enrichment-queue")
def get_enrichment_queue(
    estado: Optional[str] = Query(None, description="Filtrar por estado: PENDIENTE, EN_PROCESO, ENRIQUECIDO, NO_ENCONTRADO, ERROR, SINCRONIZADO_DSPACE"),
    tipo_falencia: Optional[str] = Query(None, description="Filtrar por falencia: SIN_ABSTRACT_CON_DOI, SIN_DOI_NI_ABSTRACT, etc."),
    page: int = Query(0, ge=0, description="Número de página"),
    size: int = Query(50, ge=1, le=200, description="Cantidad de registros por página"),
    db: Session = Depends(get_db)
):
    """
    Retorna publicaciones en la cola de enriquecimiento con filtros y paginación para el dashboard.
    """
    from app.models.db_models import DSpaceEnrichmentQueue
    query = db.query(DSpaceEnrichmentQueue)
    if estado:
        query = query.filter(DSpaceEnrichmentQueue.estado == estado)
    if tipo_falencia:
        query = query.filter(DSpaceEnrichmentQueue.tipo_falencia == tipo_falencia)

    total = query.count()
    items = query.order_by(DSpaceEnrichmentQueue.id.asc()).offset(page * size).limit(size).all()
    return {
        "total": total,
        "page": page,
        "size": size,
        "items": items
    }

@router.get("/enrichment-queue/stats")
def get_enrichment_queue_stats(
    db: Session = Depends(get_db)
):
    """
    Retorna estadísticas agregadas de la cola de enriquecimiento agrupadas por estado para los KPIs del Dashboard.
    """
    from app.models.db_models import DSpaceEnrichmentQueue
    from sqlalchemy import func
    stats = db.query(DSpaceEnrichmentQueue.estado, func.count(DSpaceEnrichmentQueue.id)).group_by(DSpaceEnrichmentQueue.estado).all()
    total = db.query(func.count(DSpaceEnrichmentQueue.id)).scalar() or 0
    return {
        "total_en_cola": total,
        "por_estado": {estado: count for estado, count in stats}
    }

@router.post("/enrich/{item_id}")
async def enrich_item(
    item_id: int,
    classify_with_ai: bool = Query(True, description="Ejecutar clasificación temática OCDE y ODS con IA (Ollama)"),
    db: Session = Depends(get_db)
):
    """
    Enriquece un ítem individual de la cola por su ID.
    Recupera abstract, keywords, financiamiento y derechos desde fuentes académicas,
    y opcionalmente clasifica en áreas OCDE y ODS usando el LLM (Ollama).
    """
    from app.services.enrichment_service import EnrichmentService
    service = EnrichmentService()
    resultado = await service.enrich_item_by_id(item_id, db, classify_with_ai=classify_with_ai)
    if not resultado:
        raise HTTPException(status_code=404, detail=f"No se encontró el registro con ID {item_id} en la cola de enriquecimiento.")
    return resultado

@router.post("/enrich-by-uuid/{dspace_uuid}")
async def enrich_item_by_uuid(
    dspace_uuid: str,
    classify_with_ai: bool = Query(True, description="Ejecutar clasificación temática OCDE y ODS con IA (Ollama)"),
    db: Session = Depends(get_db)
):
    """
    Enriquece un ítem individual de la cola por su UUID de DSpace.
    """
    from app.services.enrichment_service import EnrichmentService
    service = EnrichmentService()
    resultado = await service.enrich_item_by_uuid(dspace_uuid, db, classify_with_ai=classify_with_ai)
    if not resultado:
        raise HTTPException(status_code=404, detail=f"No se encontró el registro con UUID {dspace_uuid} en la cola de enriquecimiento.")
    return resultado

@router.post("/enrich-next")
async def enrich_next_batch(
    limit: int = Query(1, ge=1, le=50, description="Cantidad de registros pendientes a enriquecer en este lote"),
    classify_with_ai: bool = Query(True, description="Ejecutar clasificación temática OCDE y ODS con IA (Ollama)"),
    db: Session = Depends(get_db)
):
    """
    Toma los siguientes N registros en estado PENDIENTE de la cola y ejecuta el pipeline de enriquecimiento.
    Ideal para procesar y probar en lotes controlados (1, 5, 10 ítems).
    """
    from app.services.enrichment_service import EnrichmentService
    service = EnrichmentService()
    return await service.enrich_batch(limit=limit, estado_filtro="PENDIENTE", classify_with_ai=classify_with_ai, db=db)

@router.post("/generate-vriic-sample")
async def generate_vriic_sample(
    sample_size: int = Query(35, ge=5, le=50, description="Cantidad de publicaciones clasificadas para la muestra (alrededor de 30 a 40)"),
    output_filename: str = Query("muestra_clasificaciones_vriic.xlsx", description="Nombre del archivo Excel a generar en la raíz del proyecto"),
    force_reclassify: bool = Query(False, description="Si es True, fuerza la reclasificación con IA ignorando y sobrescribiendo las previas"),
    db: Session = Depends(get_db)
):
    """
    Genera una muestra de 30 a 40 publicaciones clasificadas (OCDE y ODS)
    a partir de registros de dspace_enrichment_queue con título y resumen original.
    Guarda las clasificaciones en la base de datos y exporta el archivo Excel en la raíz del proyecto para validación con la VRIIC.
    Si force_reclassify=True, vuelve a ejecutar el LLM en todos los ítems de la muestra.
    """
    from app.services.enrichment_service import EnrichmentService
    service = EnrichmentService()
    try:
        return await service.generate_vriic_sample(
            db=db,
            sample_size=sample_size,
            output_filename=output_filename,
            force_reclassify=force_reclassify
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando la muestra VRIIC: {str(e)}")

@router.post("/reset-classifications")
def reset_classifications(
    item_id: Optional[int] = Query(None, description="ID numérico del registro específico a resetear"),
    dspace_uuid: Optional[str] = Query(None, description="UUID de DSpace específico a resetear"),
    reset_all: bool = Query(False, description="Si es True, elimina las clasificaciones de TODOS los registros que tengan áreas asignadas"),
    db: Session = Depends(get_db)
):
    """
    Elimina las clasificaciones realizadas (OCDE y ODS) en 'dspace_enrichment_queue' 
    y restablece su estado a PENDIENTE o ENRIQUECIDO_FUENTES para poder volver a clasificarlas.
    """
    from app.services.enrichment_service import EnrichmentService
    service = EnrichmentService()
    return service.reset_classifications(db=db, item_id=item_id, dspace_uuid=dspace_uuid, reset_all=reset_all)

@router.get("/download-vriic-sample")
def download_vriic_sample(
    filename: str = Query("muestra_clasificaciones_vriic.xlsx", description="Nombre del archivo a descargar")
):
    """
    Descarga directamente el archivo Excel generado para la validación de la VRIIC.
    """
    import os
    from fastapi.responses import FileResponse
    file_path = os.path.abspath(filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"El archivo '{filename}' no existe aún. Ejecuta primero POST /dspace/generate-vriic-sample.")
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )