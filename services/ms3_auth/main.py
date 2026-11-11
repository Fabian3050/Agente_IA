import sys
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

COMMON_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "common"))
if os.path.exists(COMMON_DIR) and COMMON_DIR not in sys.path:
    sys.path.insert(0, os.path.abspath(os.path.join(CURRENT_DIR, "..")))

from fastapi import FastAPI
from common.database import Base, engine
from api.audit_router import router as audit_router
from api.auth_router import router as auth_router

app = FastAPI(
    title="MS3: Gestión de Usuarios, RBAC y Auditoría Inmutable",
    description="Microservicio 3 - Autenticación institucional, verificación de roles y bitácora INSERT-only.",
    version="3.0.0"
)

app.include_router(audit_router)
app.include_router(auth_router)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"service": "ms3_auth", "status": "healthy", "port": 8003}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)
