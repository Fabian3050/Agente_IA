import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from common.database import get_db, Base, engine
from models import RetrievalRequest, RetrievalResponse, ExternalAPISource
from services.retrieval_service import MS1RetrievalWorker
from api.metadata_router import router as metadata_router
from api.unpaywall_router import router as unpaywall_router

app = FastAPI(
    title="MS1: Recuperación de Metadatos",
    description="Microservicio 1 - Consultas asíncronas a APIs científicas, Fuzzy Matching y proveniencia atómica de candidatos.",
    version="3.0.0"
)

worker = MS1RetrievalWorker()

# Registrar routers trasladados desde app/
app.include_router(metadata_router)
app.include_router(unpaywall_router)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


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
