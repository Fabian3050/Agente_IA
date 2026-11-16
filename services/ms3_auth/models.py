import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Boolean, JSON, Text, DateTime, ForeignKey, Uuid
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

try:
    from common.database import Base
except ImportError:
    from services.common.database import Base


# =============================================================================
# MODELOS SQLALCHEMY PROPIETARIOS DE MS3
# =============================================================================

class Role(Base):
    __tablename__ = "role"
    __table_args__ = {'extend_existing': True}

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False)       # 'Academico', 'Curador_VRIIC', 'Admin'
    description = Column(String(255), nullable=True)

    users = relationship(lambda: User, back_populates="role", overlaps="role,users")


class User(Base):
    __tablename__ = "user"
    __table_args__ = {'extend_existing': True}

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    id_role = Column(Uuid, ForeignKey("role.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    sub = Column(String(255), unique=True, nullable=True, index=True)  # Subject OIDC / SSO USACH
    orcid = Column(String(50), nullable=True)
    dspace_person_id = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime, nullable=True)

    role = relationship(lambda: Role, back_populates="users", overlaps="role,users")
    audit_logs = relationship(lambda: AuditLog, back_populates="user", overlaps="audit_logs,user")


class AuditLog(Base):
    """
    Bitácora inmutable de decisiones humanas de curaduría (INSERT-only).
    Se revoca UPDATE y DELETE para garantizar inmutabilidad según Sección 2.5.
    """
    __tablename__ = "audit_log"
    __table_args__ = {'extend_existing': True}

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    id_user = Column(Uuid, ForeignKey("user.id"), nullable=False, index=True)
    id_item_enrichment = Column(Uuid, nullable=False, index=True)
    action = Column(String(50), nullable=False)                  # 'Aprobar', 'Rechazar', 'Editar', 'Invalidar'
    previous_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = relationship(lambda: User, back_populates="audit_logs", overlaps="audit_logs,user")


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
    sub: Optional[str] = None
    orcid: Optional[str] = None
    dspace_person_id: Optional[str] = None
    is_active: bool
    last_login: Optional[datetime] = None


class TokenResponseDTO(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserDTO


class OIDCCallbackRequest(BaseModel):
    code: str
    state: Optional[str] = None


class OIDCTokenExchangeRequest(BaseModel):
    id_token: str = Field(description="JWT ID Token emitido por el proveedor OIDC institucional")


class MockLoginRequest(BaseModel):
    email: str
    role_name: str = "Curador_VRIIC"  # 'Academico', 'Curador_VRIIC', 'Admin'
    name: str = "Usuario"
    last_name: str = "Institucional"
    orcid: Optional[str] = None
    dspace_person_id: Optional[str] = None


class CreateUserRequest(BaseModel):
    email: str = Field(description="Correo electrónico institucional")
    name: str = Field(description="Nombres")
    last_name: str = Field(description="Apellidos")
    role_name: str = Field(default="Curador_VRIIC", description="'Admin', 'Curador_VRIIC' o 'Academico'")
    orcid: Optional[str] = Field(default=None, description="Identificador persistente ORCID")
    dspace_person_id: Optional[str] = Field(default=None, description="UUID del perfil de persona en DSpace-CRIS")
    sub: Optional[str] = Field(default=None, description="Subject OIDC del proveedor institucional")
    is_active: bool = Field(default=True, description="Estado de activación del usuario")


class TokenIntrospectRequest(BaseModel):
    token: str


class TokenIntrospectResponse(BaseModel):
    active: bool
    user_id: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None
    orcid: Optional[str] = None
    dspace_person_id: Optional[str] = None
    exp: Optional[int] = None
