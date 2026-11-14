import sys
import os
import uuid
import logging

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

COMMON_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "common"))
if os.path.exists(COMMON_DIR) and COMMON_DIR not in sys.path:
    sys.path.insert(0, os.path.abspath(os.path.join(CURRENT_DIR, "..")))

from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from common.database import get_db, Base, engine, SessionLocal
from common.messaging import start_background_consumer
from models import DetectItemRequest, CurateDecisionRequest, ItemEnrichment, Status
from services.orchestrator_service import MS4Orchestrator
from services.seed_service import run_full_seeding
from api.proposals_v3_router import router as proposals_v3_router
from api.dspace_router import router as dspace_router
from api.item_router import router as item_router

logger = logging.getLogger(__name__)

app = FastAPI(
    title="MS4: Conexión, Orquestación e Integración DSpace-CRIS",
    description="Microservicio 4 - Gateway principal, ciclo de vida formal (12 estados), proveniencia atómica y exportación CSV segura.",
    version="3.0.0"
)

orchestrator = MS4Orchestrator()

# Registrar routers trasladados desde app/
app.include_router(proposals_v3_router)
app.include_router(dspace_router)
app.include_router(item_router)


def process_rabbitmq_response(payload: dict):
    """Callback para procesar respuestas de recuperación emitidas por MS1 vía RabbitMQ."""
    db = SessionLocal()
    try:
        orchestrator.handle_retrieval_response(db, payload)
        logger.info(f"[MS4] Procesada respuesta RabbitMQ para ítem: {payload.get('item_id')}")
    except Exception as e:
        logger.error(f"[MS4] Error procesando respuesta RabbitMQ en MS4: {e}")
    finally:
        db.close()


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    try:
        db = SessionLocal()
        run_full_seeding(db)
        db.close()
    except Exception as e:
        logger.warning(f"[MS4] Advertencia al sembrar catálogo de estados: {e}")

    try:
        start_background_consumer("dspace.retrieval.responses", process_rabbitmq_response)
        logger.info("[MS4] Consumidor de RabbitMQ iniciado para 'dspace.retrieval.responses'.")
    except Exception as e:
        logger.warning(f"[MS4] Advertencia al iniciar consumidor de RabbitMQ: {e}")


@app.get("/health")
def health():
    return {"service": "ms4_orchestrator", "status": "healthy", "port": 8000}


@app.post("/detect")
def detect_publication(payload: DetectItemRequest, db: Session = Depends(get_db)):
    """
    Bloque 1: Monitoreo e Idempotencia temprana.
    Evalúa si la publicación tiene una propuesta activa antes de iniciar trabajo.
    """
    item, msg = orchestrator.handle_detection(
        db=db,
        uuid_dspace=payload.uuid_dspace,
        doi=payload.doi,
        title=payload.title,
        last_modified_dspace=payload.last_modified_dspace,
        force_reprocess=payload.force_reprocess
    )
    return {
        "item_id": str(item.id) if item else None,
        "status": item.status.name if item and item.status else None,
        "message": msg
    }


@app.post("/pipeline/{item_id}")
async def execute_pipeline(item_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Orquesta las llamadas a MS1 (Recuperación) y MS2 (Clasificación).
    """
    item = db.query(ItemEnrichment).filter(ItemEnrichment.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")

    result = await orchestrator.run_pipeline_for_item(db, item)
    return result


@app.post("/curate/{item_id}")
async def curate_publication(
    item_id: uuid.UUID,
    payload: CurateDecisionRequest,
    db: Session = Depends(get_db)
):
    """
    Bloque 4: Decisión de curaduría humana con revalidación de concurrencia y registro en MS3.
    """
    item = db.query(ItemEnrichment).filter(ItemEnrichment.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")

    result = await orchestrator.apply_curation(
        db=db,
        item=item,
        user_id=payload.user_id,
        decision=payload.decision,
        edited_fields=payload.edited_fields,
        rejection_reason=payload.rejection_reason,
        dspace_live_last_modified=payload.dspace_live_last_modified
    )
    return result


@app.post("/export-csv")
def export_csv(db: Session = Depends(get_db)):
    """
    Bloque 5: Exportación masiva segura con CERO celdas vacías agrupadas por combinación.
    """
    batches = orchestrator.export_csv_zero_empty_cells(db)
    return {"total_batches": len(batches), "batches": batches}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
