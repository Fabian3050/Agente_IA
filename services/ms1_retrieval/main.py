import sys
import os
import uuid
import asyncio
import logging

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# Soporte para common tanto en local como dentro del contenedor Docker
COMMON_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "common"))
if os.path.exists(COMMON_DIR) and COMMON_DIR not in sys.path:
    sys.path.insert(0, os.path.abspath(os.path.join(CURRENT_DIR, "..")))

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from common.database import get_db, Base, engine, SessionLocal
from common.messaging import publish_event, start_background_consumer
from models import RetrievalRequest, RetrievalResponse, ExternalAPISource
from services.retrieval_service import MS1RetrievalWorker
from api.metadata_router import router as metadata_router
from api.unpaywall_router import router as unpaywall_router

logger = logging.getLogger(__name__)

app = FastAPI(
    title="MS1: Recuperación de Metadatos",
    description="Microservicio 1 - Consultas asíncronas a APIs científicas, Fuzzy Matching y proveniencia atómica de candidatos.",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

worker = MS1RetrievalWorker()

# Registrar routers trasladados desde app/
app.include_router(metadata_router)
app.include_router(unpaywall_router)


def process_rabbitmq_request(payload: dict):
    """Callback de RabbitMQ para procesar solicitudes asíncronas de recuperación desde MS4."""
    item_id_raw = payload.get("item_id")
    if not item_id_raw:
        return
    item_id = uuid.UUID(item_id_raw) if isinstance(item_id_raw, str) else item_id_raw
    doi = payload.get("doi")
    title = payload.get("title")
    reply_queue = payload.get("reply_queue", "dspace.retrieval.responses")

    db = SessionLocal()
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        res = loop.run_until_complete(
            worker.execute_retrieval(item_id=item_id, doi=doi, title=title, db=db)
        )
        loop.close()

        publish_event(reply_queue, {
            "item_id": str(item_id),
            "outcome": res.get("outcome"),
            "max_score": res.get("max_score"),
            "best_source": res.get("best_source"),
            "consolidated": res.get("consolidated"),
            "query_statuses": res.get("query_statuses")
        })
    except Exception as e:
        logger.error(f"[MS1] Error procesando RabbitMQ request para ítem {item_id}: {e}")
        publish_event(reply_queue, {
            "item_id": str(item_id),
            "outcome": "ERROR",
            "error": str(e)
        })
    finally:
        db.close()


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    try:
        start_background_consumer("dspace.retrieval.requests", process_rabbitmq_request)
        logger.info("[MS1] Consumidor de RabbitMQ iniciado para 'dspace.retrieval.requests'.")
    except Exception as e:
        logger.warning(f"[MS1] Advertencia al iniciar consumidor de RabbitMQ: {e}")


@app.get("/health")
def health():
    return {"service": "ms1_retrieval", "status": "healthy", "port": 8001}


@app.get("/sources")
def list_sources(db: Session = Depends(get_db)):
    """Lista las fuentes científicas externas configuradas."""
    return db.query(ExternalAPISource).all()


@app.post("/retrieve", response_model=RetrievalResponse)
async def retrieve_metadata(payload: RetrievalRequest, db: Session = Depends(get_db)):
    """
    Ejecuta el protocolo de recuperación en Crossref, OpenAlex, Unpaywall, Europe PMC y S2.
    Registra exclusivamente en Candidate_Match y External_API_Source.
    """
    try:
        result = await worker.execute_retrieval(
            item_id=payload.item_id,
            doi=payload.doi,
            title=payload.title,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en recuperación MS1: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
