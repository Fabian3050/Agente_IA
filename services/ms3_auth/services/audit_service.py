import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from models import AuditLog, User, Role


class MS3AuditWorker:
    """
    Microservicio 3: Gestión inmutable de auditoría (INSERT-only).
    Escribe exclusivamente en Audit_Log, User y Role.
    """

    def record_action(
        self,
        db: Session,
        user_id: uuid.UUID,
        item_id: uuid.UUID,
        action: str,
        previous_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        rejection_reason: Optional[str] = None
    ) -> AuditLog:
        valid_actions = ["Aprobar", "Rechazar", "Editar", "Invalidar"]
        if action not in valid_actions:
            raise ValueError(f"Acción '{action}' no permitida. Válidas: {valid_actions}")

        entry = AuditLog(
            id_user=user_id,
            id_item_enrichment=item_id,
            action=action,
            previous_value=previous_value,
            new_value=new_value,
            rejection_reason=rejection_reason,
            timestamp=datetime.utcnow()
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    def get_logs_for_item(self, db: Session, item_id: uuid.UUID) -> List[AuditLog]:
        return db.query(AuditLog).filter(AuditLog.id_item_enrichment == item_id).order_by(AuditLog.timestamp.desc()).all()

    def verify_permission(self, db: Session, user_id: uuid.UUID, required_role: str) -> bool:
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user or not user.role:
            return False
        if user.role.name == "Admin":
            return True
        return user.role.name == required_role

