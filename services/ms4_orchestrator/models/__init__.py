import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey, Uuid
)
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

try:
    from common.database import Base
except ImportError:
    from services.common.database import Base

try:
    from models.item_model import Item
except ImportError:
    from services.ms4_orchestrator.models.item_model import Item


# =============================================================================
# MODELOS SQLALCHEMY PROPIETARIOS DE MS4
# =============================================================================

class Status(Base):
    __tablename__ = "status"
    __table_args__ = {'extend_existing': True}

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
    __table_args__ = {'extend_existing': True}

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
    __table_args__ = {'extend_existing': True}

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
    __table_args__ = {'extend_existing': True}

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    id_item_enrichment = Column(Uuid, ForeignKey("item_enrichment.id"), nullable=False, index=True)
    id_category = Column(Integer, nullable=False, index=True)
    origin = Column(String(20), nullable=False)
    priority_order = Column(Integer, nullable=False)
    confidence_score = Column(Float, nullable=True)

    item_enrichment = relationship("ItemEnrichment", back_populates="categories")


class Job(Base):
    __tablename__ = "job"
    __table_args__ = {'extend_existing': True}

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    id_item_enrichment = Column(Uuid, ForeignKey("item_enrichment.id"), nullable=False, index=True)
    stage = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, index=True)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    next_run_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    item_enrichment = relationship("ItemEnrichment", back_populates="jobs")


class DSpaceSyncLog(Base):
    __tablename__ = "dspace_sync_log"
    __table_args__ = {'extend_existing': True}

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    id_item_enrichment = Column(Uuid, ForeignKey("item_enrichment.id"), nullable=False, index=True)
    http_status_code = Column(Integer, nullable=True)
    sync_type = Column(String(50), nullable=False)
    synced_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    item_enrichment = relationship("ItemEnrichment", back_populates="sync_logs")


# Modelos legacy para compatibilidad con dashboards de auditoría histórica
class DSpaceMetricsHistory(Base):
    __tablename__ = "dspace_metrics_history"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(DateTime, default=datetime.utcnow, index=True)
    total_revisados = Column(Integer, default=0)
    total_valid_resource_types = Column(Integer, default=0)
    total_sin_title = Column(Integer, default=0)
    total_sin_abstract = Column(Integer, default=0)
    total_no_abstract_disponible = Column(Integer, default=0)
    total_missing_abs_org_art = Column(Integer, default=0)
    total_sin_doi = Column(Integer, default=0)
    total_sin_subjects = Column(Integer, default=0)
    total_pub_sin_doi_sin_abs = Column(Integer, default=0)
    total_sin_abstract_con_doi = Column(Integer, default=0)
    total_sin_doi_ni_abstract = Column(Integer, default=0)


class DSpaceEnrichmentQueue(Base):
    __tablename__ = "dspace_enrichment_queue"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    dspace_uuid = Column(String, unique=True, index=True, nullable=False)
    doi = Column(String, index=True, nullable=True)
    titulo = Column(Text, nullable=True)
    tipo_recurso = Column(String, nullable=True)
    tipo_falencia = Column(String, nullable=True)
    estado = Column(String, index=True, default="PENDIENTE")
    fuente_enriquecimiento = Column(String, nullable=True)
    abstract_enriquecido = Column(Text, nullable=True)
    palabras_clave = Column(JSON, nullable=True)
    fuente_financiamiento = Column(JSON, nullable=True)
    derechos_acceso = Column(String, nullable=True)
    area_ocde = Column(JSON, nullable=True)
    area_ods = Column(JSON, nullable=True)
    metadatos_recuperados = Column(JSON, nullable=True)
    resumen_original = Column(Text, nullable=True)
    intentos = Column(Integer, default=0)
    mensaje_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


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

