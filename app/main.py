from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import engine, Base
from app.api.item_router import router as item_router
from app.api.metadata_router import router as metadata_router
from app.api.ollama_router import router as ollama_router
from app.api.classification_router import router as classification_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Importamos los modelos de SQLAlchemy para que se registren en la Base
    from app.models.db_models import DoiRecord, DocumentMetadata
    
    # Crea todas las tablas en la BD si no existen
    Base.metadata.create_all(bind=engine)
    yield
    # Lógica de apagado (si fuera necesaria)

app = FastAPI(
    title="My FastAPI Backend",
    description="A basic FastAPI backend setup with Modular Architecture and Metadata Integrations",
    version="1.0.0",
    lifespan=lifespan
)

# Registramos los controladores
app.include_router(item_router)
app.include_router(metadata_router)
app.include_router(ollama_router)
app.include_router(classification_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Modular FastAPI Backend"}
