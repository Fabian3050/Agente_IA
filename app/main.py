from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import engine, Base, SessionLocal
from app.api.item_router import router as item_router
from app.api.metadata_router import router as metadata_router
from app.api.ollama_router import router as ollama_router
from app.api.classification_router import router as classification_router
from app.api.dspace_router import router as dspace_router
from app.api.unpaywall_router import router as unpaywall_router
from app.api.proposals_v3_router import router as proposals_v3_router
from app.services.seed_service import run_full_seeding


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Crear todas las tablas en la BD si no existen
    Base.metadata.create_all(bind=engine)
    
    # 2. Inicializar catálogos estandarizados (12 Estados, Fuentes, Roles y Categorías OCDE/ODS)
    db = SessionLocal()
    try:
        run_full_seeding(db)
    except Exception as e:
        print(f"[Warning] Seeding en startup falló o ya fue completado: {e}")
    finally:
        db.close()

    yield
    # Lógica de apagado


app = FastAPI(
    title="Agente IA DSpace-CRIS Backend (Versión 3.0)",
    description="Arquitectura de Microservicios para Enriquecimiento, Clasificación y Curaduría de Metadatos DSpace-CRIS",
    version="3.0.0",
    lifespan=lifespan
)

# Registramos los controladores
app.include_router(proposals_v3_router)
app.include_router(item_router)
app.include_router(metadata_router)
app.include_router(ollama_router)
app.include_router(classification_router)
app.include_router(dspace_router)
app.include_router(unpaywall_router)


@app.get("/")
def read_root():
    return {
        "system": "Agente IA DSpace-CRIS",
        "version": "3.0.0",
        "architecture": "Microservicios (MS1: Recuperación, MS2: Clasificación, MS3: Usuarios/RBAC, MS4: Integración)",
        "status": "online"
    }
