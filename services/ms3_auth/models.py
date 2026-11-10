import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Boolean, JSON, Text, DateTime, ForeignKey, Uuid
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

from common.database import Base


# =============================================================================
# MODELOS SQLALCHEMY PROPIETARIOS DE MS3
# =============================================================================

class Role(Base):
    __tablename__ = "role"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False)       # 'Academico', 'Curador_VRIIC', 'Admin'
    description = Column(String(255), nullable=True)

    users = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "user"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    id_role = Column(Uuid, ForeignKey("role.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    orcid = Column(String(50), nullable=True)
    dspace_person_id = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    role = relationship("Role", back_populates="users")
    audit_logs = relationship("AuditLog", back_populates="user")


class AuditLog(Base):
    """
    Bitácora inmutable de decisiones humanas de curaduría (INSERT-only).
    Se revoca UPDATE y DELETE para garantizar inmutabilidad.
    """
    __tablename__ = "audit_log"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    id_user = Column(Uuid, ForeignKey("user.id"), nullable=False, index=True)
    id_item_enrichment = Column(Uuid, nullable=False, index=True)
    action = Column(String(50), nullable=False)                  # 'Aprobar', 'Rechazar', 'Editar', 'Invalidar'
    previous_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = relationship("User", back_populates="audit_logs")


# =============================================================================
# ESQUEMAS PYDANTIC (DTOs)
# =============================================================================

class AuditLogCreateRequest(BaseModel):
    user_id: uuid.UUID
    item_id: uuid.UUID
    action: str = Field(description="'Aprobar', 'Rechazar', 'Editar', 'Invalidar'")
    previous_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    rejection_reason: Optional[str] = None


class AuditLogDTO(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    item_id: uuid.UUID
    action: str
    previous_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    rejection_reason: Optional[str] = None
    timestamp: datetime


class UserDTO(BaseModel):
    id: uuid.UUID
    name: str
    last_name: str
    email: str
    role_name: str
    orcid: Optional[str] = None
    dspace_person_id: Optional[str] = None
    is_active: bool

