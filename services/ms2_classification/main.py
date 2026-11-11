import sys
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

COMMON_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "common"))
if os.path.exists(COMMON_DIR) and COMMON_DIR not in sys.path:
    sys.path.insert(0, os.path.abspath(os.path.join(CURRENT_DIR, "..")))

from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from common.database import get_db, Base, engine
from models import ClassificationRequest, ClassificationResultResponse, Category
from services.classification_service import MS2ClassificationWorker
from api.classification_router import router as classification_router
from api.ollama_router import router as ollama_router

app = FastAPI(
    title="MS2: Clasificación Área OCDE / ODS",
    description="Microservicio 2 - Inferencia semántica con LLM local Ollama, modelos estructurados Pydantic y bitácora de inferencia.",
    version="3.0.0"
)

worker = MS2ClassificationWorker()

# Registrar routers trasladados desde app/
app.include_router(classification_router)
app.include_router(ollama_router)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"service": "ms2_classification", "status": "healthy", "port": 8002}


@app.get("/categories")
def list_categories(
    scheme: str = Query("OCDE", description="'OCDE' o 'ODS'"),
    db: Session = Depends(get_db)
):
    """Consulta el catálogo oficial parametrizado de categorías."""
    return db.query(Category).filter(Category.scheme == scheme).all()


@app.post("/classify", response_model=ClassificationResultResponse)
async def classify_publication(payload: ClassificationRequest, db: Session = Depends(get_db)):
    """
    Ejecuta la inferencia semántica con Llama 3.2 (3B) en Ollama a T=0.0.
    Escribe exclusivamente en LLM_Classification_Log y Category.
    """
    try:
        result = await worker.execute_classification(
            item_id=payload.item_id,
            title=payload.title,
            abstract=payload.abstract,
            keywords=payload.keywords,
            db=db,
            temperature=payload.temperature,
            repetition_number=payload.repetition_number
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en clasificación MS2: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
