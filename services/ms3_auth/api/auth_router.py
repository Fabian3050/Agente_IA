import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from common.database import get_db
from models import User, Role, UserDTO
from services.audit_service import MS3AuditWorker

router = APIRouter(prefix="/auth", tags=["Authentication & RBAC"])
audit_worker = MS3AuditWorker()

@router.get("/verify-role")
def verify_role(
    user_id: uuid.UUID = Query(...),
    required_role: str = Query(...),
    db: Session = Depends(get_db)
):
    """Verifica si el usuario cuenta con el rol requerido (RBAC: Academico, Curador_VRIIC, Admin)."""
    allowed = audit_worker.verify_permission(db, user_id, required_role)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permiso denegado: El usuario no cuenta con el rol '{required_role}'."
        )
    return {"user_id": str(user_id), "role": required_role, "authorized": True}

@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [
        {
            "id": str(u.id),
            "name": u.name,
            "last_name": u.last_name,
            "email": u.email,
            "role": u.role.name if u.role else None,
            "orcid": u.orcid,
            "dspace_person_id": u.dspace_person_id,
            "is_active": u.is_active
        }
        for u in users
    ]

