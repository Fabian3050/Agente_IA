import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.db_models import (
    User, Role, AuditLog, ItemEnrichment
)


class CurationAuditServiceMS3:
    """
    Microservicio 3: Gestión de Usuarios, RBAC y Auditoría Inmutable (MS3).
    Escribe exclusivamente en las tablas User, Role y Audit_Log.
    """

    def record_curation_action(
        self,
        db: Session,
        user_id: Any,
        item_id: Any,
        action: str,  # 'Aprobar', 'Rechazar', 'Editar', 'Invalidar'
        previous_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        rejection_reason: Optional[str] = None
    ) -> AuditLog:
        """
        Registra un evento inmutable en la bitácora histórica de auditoría.
        Garantiza proveniencia y trazabilidad inalterable de decisiones humanas.
        """
        valid_actions = ["Aprobar", "Rechazar", "Editar", "Invalidar"]
        if action not in valid_actions:
            raise ValueError(f"Acción inválida '{action}'. Acciones válidas: {valid_actions}")

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

    def check_user_role(self, db: Session, user_id: Any, required_role: str) -> bool:
        """Verifica los permisos RBAC de un usuario."""
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user or not user.role:
            return False
        if user.role.name == "Admin":
            return True  # Admin tiene todos los permisos
        return user.role.name == required_role

