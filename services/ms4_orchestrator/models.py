import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey, Uuid
)
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

from common.database import Base


# =============================================================================
# MODELOS SQLALCHEMY PROPIETARIOS DE MS4
# =============================================================================

class Status(Base):
    __tablename__ = "status"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)

    items = relationship("ItemEnrichment", back_populates="status")


class ProposalStatus:
    DETECTADA = "Detectada"
    EN_RECUPERACION = "En_recuperacion"
    COINCIDENCIA_DUDOSA = "Coincidencia_dudosa"
    EN_CLASIFICACION = "En_clasificacion"
    EN_REINTENTO = "En_reintento"
    EN_REVISION = "En_revision"
    INVALIDADA = "Invalidada"
    RECHAZADA = "Rechazada"
    APROBADA = "Aprobada"
    EXPORTADA = "Exportada"
    CARGADA = "Cargada"
    CERRADA = "Cerrada"


class ItemEnrichment(Base):
    __tablename__ = "item_enrichment"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    id_status = Column(Integer, ForeignKey("status.id"), nullable=False, index=True)
    uuid_dspace = Column(String(100), unique=True, nullable=False, index=True)
    doi = Column(String(150), nullable=True, index=True)
    title = Column(String(1000), nullable=True)
    abstract = Column(Text, nullable=True)
    author_keywords = Column(Text, nullable=True)
    automated_concepts = Column(Text, nullable=True)
    oa_status = Column(String(50), nullable=True)
    license = Column(String(100), nullable=True)
    version_type = Column(String(50), nullable=True)
    funding_agency = Column(String(255), nullable=True)
    funding_id = Column(String(100), nullable=True)
    funding_grant_number = Column(String(100), nullable=True)
    last_modified_dspace = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    status = relationship("Status", back_populates="items")
    field_proposals = relationship("FieldProposal", back_populates="item_enrichment", cascade="all, delete-orphan")
    categories = relationship("ItemCategory", back_populates="item_enrichment", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="item_enrichment", cascade="all, delete-orphan")
    sync_logs = relationship("DSpaceSyncLog", back_populates="item_enrichment", cascade="all, delete-orphan")


class FieldProposal(Base):
    __tablename__ = "field_proposal"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    id_item_enrichment = Column(Uuid, ForeignKey("item_enrichment.id"), nullable=False, index=True)
    field_name = Column(String(100), nullable=False)
    original_dspace_value = Column(Text, nullable=True)
    proposed_value = Column(Text, nullable=True)
    source = Column(String(100), nullable=True)
    rule_applied = Column(String(255), nullable=True)
    retrieved_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    final_value = Column(Text, nullable=True)
    is_edited_by_curator = Column(Boolean, default=False, nullable=False)

    item_enrichment = relationship("ItemEnrichment", back_populates="field_proposals")


class ItemCategory(Base):
    __tablename__ = "item_category"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    id_item_enrichment = Column(Uuid, ForeignKey("item_enrichment.id"), nullable=False, index=True)
    id_category = Column(Integer, nullable=False, index=True)
    origin = Column(String(20), nullable=False)                  # 'LLM' / 'Curador'
    priority_order = Column(Integer, nullable=False)             # 1 o 2
    confidence_score = Column(Float, nullable=True)

    item_enrichment = relationship("ItemEnrichment", back_populates="categories")


class Job(Base):
    __tablename__ = "job"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    id_item_enrichment = Column(Uuid, ForeignKey("item_enrichment.id"), nullable=False, index=True)
    stage = Column(String(50), nullable=False)                   # 'Recuperacion', 'Clasificacion', 'Sync'
    status = Column(String(50), nullable=False, index=True)      # 'Pendiente', 'En_Progreso', 'Fallido', 'Completado'
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    next_run_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    item_enrichment = relationship("ItemEnrichment", back_populates="jobs")


class DSpaceSyncLog(Base):
    __tablename__ = "dspace_sync_log"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    id_item_enrichment = Column(Uuid, ForeignKey("item_enrichment.id"), nullable=False, index=True)
    http_status_code = Column(Integer, nullable=True)
    sync_type = Column(String(50), nullable=False)               # 'Export_CSV', 'REST_PATCH', 'Verification'
    synced_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    item_enrichment = relationship("ItemEnrichment", back_populates="sync_logs")


# =============================================================================
# ESQUEMAS PYDANTIC (DTOs)
# =============================================================================

class DetectItemRequest(BaseModel):
    uuid_dspace: str
    doi: Optional[str] = None
    title: Optional[str] = None
    last_modified_dspace: Optional[datetime] = None
    force_reprocess: bool = False


class CurateDecisionRequest(BaseModel):
    user_id: uuid.UUID
    decision: str = Field(description="'Aprobar', 'Rechazar' o 'Editar'")
    edited_fields: Optional[Dict[str, str]] = None
    rejection_reason: Optional[str] = None
    dspace_live_last_modified: Optional[datetime] = None

