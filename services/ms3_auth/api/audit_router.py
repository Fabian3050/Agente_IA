import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from common.database import get_db
from models import AuditLogCreateRequest, AuditLogDTO
from services.audit_service import MS3AuditWorker

router = APIRouter(prefix="/audit", tags=["Audit Log"])
audit_worker = MS3AuditWorker()

@router.post("/", status_code=status.HTTP_201_CREATED)
def record_audit(payload: AuditLogCreateRequest, db: Session = Depends(get_db)):
    """
    Registra una decisión de curaduría humana de manera inmutable (INSERT-only).
    """
    try:
        entry = audit_worker.record_action(
            db=db,
            user_id=payload.user_id,
            item_id=payload.item_id,
            action=payload.action,
            previous_value=payload.previous_value,
            new_value=payload.new_value,
            rejection_reason=payload.rejection_reason
        )
        return {
            "id": str(entry.id),
            "status": "recorded",
            "timestamp": entry.timestamp.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{item_id}")
def get_audit_trail(item_id: uuid.UUID, db: Session = Depends(get_db)):
    """Recupera la trazabilidad inmutable de un ítem para auditoría institucional."""
    entries = audit_worker.get_logs_for_item(db, item_id)
    return [
        {
            "id": str(e.id),
            "user_id": str(e.id_user),
            "action": e.action,
            "previous_value": e.previous_value,
            "new_value": e.new_value,
            "rejection_reason": e.rejection_reason,
            "timestamp": e.timestamp.isoformat()
        }
        for e in entries
    ]

