import sys
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

COMMON_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "common"))
if os.path.exists(COMMON_DIR) and COMMON_DIR not in sys.path:
    sys.path.insert(0, os.path.abspath(os.path.join(CURRENT_DIR, "..")))

from fastapi import FastAPI
from sqlalchemy import text
from common.database import Base, engine, SessionLocal
from api.audit_router import router as audit_router
from api.auth_router import router as auth_router
from services.seed_service import seed_roles, seed_initial_users

app = FastAPI(
    title="MS3: Gestión de Usuarios, RBAC y Auditoría Inmutable",
    description="Microservicio 3 - Autenticación institucional OpenID Connect / OAuth 2.0, verificación de roles RBAC y bitácora INSERT-only.",
    version="3.0.0"
)

app.include_router(audit_router)
app.include_router(auth_router)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

    # Migración idempotente para asegurar columnas OIDC en tabla 'user'
    try:
        with engine.connect() as conn:
            conn.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS sub VARCHAR(255);'))
            conn.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS last_login TIMESTAMP;'))
            conn.execute(text('CREATE UNIQUE INDEX IF NOT EXISTS ix_user_sub ON "user" (sub);'))
            conn.commit()
    except Exception as e:
        print(f"[MS3] Esquema 'user' actualizado / advertencia: {e}")

    try:
        db = SessionLocal()
        seed_roles(db)
        seed_initial_users(db)
        db.close()
    except Exception as e:
        print(f"[MS3] Advertencia sembrando usuarios/roles: {e}")


@app.get("/health")
def health():
    return {"service": "ms3_auth", "status": "healthy", "port": 8003}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)
