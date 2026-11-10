import uuid
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey, Index, Uuid
)
from sqlalchemy.orm import relationship
from app.database import Base


# =============================================================================
# CATÁLOGO DE ESTADOS FORMALES (MS4) - 12 ESTADOS UNÍVOCOS
# =============================================================================

class Status(Base):
    """
    Catálogo de los 12 estados formales del ciclo de vida de propuestas.
    Dueño: MS4 (Conexión e Integración DSpace-CRIS)
    """
    __tablename__ = "status"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)

    items = relationship("ItemEnrichment", back_populates="status")


# Constantes de estados para evitar strings mágicos
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

    ALL = [
        DETECTADA, EN_RECUPERACION, COINCIDENCIA_DUDOSA, EN_CLASIFICACION,
        EN_REINTENTO, EN_REVISION, INVALIDADA, RECHAZADA, APROBADA,
        EXPORTADA, CARGADA, CERRADA
    ]


# =============================================================================
# ENTIDAD PRINCIPAL DE ENRIQUECIMIENTO (MS4)
# =============================================================================

class ItemEnrichment(Base):
    """
    Entidad principal de la propuesta de enriquecimiento.
    Dueño: MS4 (Conexión e Integración DSpace-CRIS)
    """
    __tablename__ = "item_enrichment"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    id_status = Column(Integer, ForeignKey("status.id"), nullable=False, index=True)
    uuid_dspace = Column(String(100), unique=True, nullable=False, index=True)
    doi = Column(String(150), nullable=True, index=True)
    title = Column(String(1000), nullable=True)
    abstract = Column(Text, nullable=True)
    author_keywords = Column(Text, nullable=True)        # dc.subject
    automated_concepts = Column(Text, nullable=True)     # cris.concept
    oa_status = Column(String(50), nullable=True)        # Gold, Green, Bronze, Hybrid, Closed
    license = Column(String(100), nullable=True)         # ej. CC-BY
    version_type = Column(String(50), nullable=True)     # Preprint, Postprint, PublishedVersion
    funding_agency = Column(String(255), nullable=True)
    funding_id = Column(String(100), nullable=True)
    funding_grant_number = Column(String(100), nullable=True)
    last_modified_dspace = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relaciones
    status = relationship("Status", back_populates="items")
    field_proposals = relationship("FieldProposal", back_populates="item_enrichment", cascade="all, delete-orphan")
    categories = relationship("ItemCategory", back_populates="item_enrichment", cascade="all, delete-orphan")
    candidate_matches = relationship("CandidateMatch", back_populates="item_enrichment", cascade="all, delete-orphan")
    classification_logs = relationship("LLMClassificationLog", back_populates="item_enrichment", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="item_enrichment", cascade="all, delete-orphan")
    sync_logs = relationship("DSpaceSyncLog", back_populates="item_enrichment", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="item_enrichment")


# =============================================================================
# PROVENIENCIA ATÓMICA POR CAMPO (MS4)
# =============================================================================

class FieldProposal(Base):
    """
    Trazabilidad atómica y proveniencia por campo propuesto.
    Dueño: MS4 (Conexión e Integración DSpace-CRIS)
    """
    __tablename__ = "field_proposal"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    id_item_enrichment = Column(Uuid, ForeignKey("item_enrichment.id"), nullable=False, index=True)
    field_name = Column(String(100), nullable=False)     # ej. dc.description.abstract, dc.subject
    original_dspace_value = Column(Text, nullable=True)
    proposed_value = Column(Text, nullable=True)
    source = Column(String(100), nullable=True)          # Crossref, OpenAlex, etc.
    rule_applied = Column(String(255), nullable=True)
    retrieved_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    final_value = Column(Text, nullable=True)            # Consolidado tras curaduría humana
    is_edited_by_curator = Column(Boolean, default=False, nullable=False)

    item_enrichment = relationship("ItemEnrichment", back_populates="field_proposals")


# =============================================================================
# CATÁLOGO DE CATEGORÍAS (MS2) Y ASIGNACIÓN (MS4)
# =============================================================================

class Category(Base):
    """
    Catálogo oficial parametrizado (FORD OCDE 2007 y ODS ONU 2015).
    Dueño: MS2 (Clasificación Área OCDE / ODS)
    """
    __tablename__ = "category"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), nullable=False, index=True)        # ej. 1.1, ODS 7
    name = Column(String(255), nullable=False)
    scheme = Column(String(20), nullable=False, index=True)      # 'OCDE' / 'ODS'
    version = Column(String(20), nullable=False)                 # '2007' / '2015'
    description = Column(Text, nullable=True)

    items = relationship("ItemCategory", back_populates="category")


class ItemCategory(Base):
    """
    Asignación relacional de categorías a ítems de enriquecimiento.
    Dueño: MS4 (Conexión e Integración DSpace-CRIS)
    """
    __tablename__ = "item_category"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    id_item_enrichment = Column(Uuid, ForeignKey("item_enrichment.id"), nullable=False, index=True)
    id_category = Column(Integer, ForeignKey("category.id"), nullable=False, index=True)
    origin = Column(String(20), nullable=False)                  # 'LLM' / 'Curador'
    priority_order = Column(Integer, nullable=False)             # 1 (principal) o 2 (secundaria)
    confidence_score = Column(Float, nullable=True)

    item_enrichment = relationship("ItemEnrichment", back_populates="categories")
    category = relationship("Category", back_populates="items")


# =============================================================================
# FUENTES EXTERNAS Y COINCIDENCIAS CANDIDATAS (MS1)
# =============================================================================

class ExternalAPISource(Base):
    """
    Catálogo de fuentes científicas externas configuradas.
    Dueño: MS1 (Recuperación de Metadatos)
    """
    __tablename__ = "external_api_source"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)      # Crossref, OpenAlex, Unpaywall, Europe PMC, Semantic Scholar
    base_url = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    matches = relationship("CandidateMatch", back_populates="external_source")


class CandidateMatch(Base):
    """
    Respuestas brutas y candidatos recuperados por fuente externa.
    Dueño: MS1 (Recuperación de Metadatos)
    """
    __tablename__ = "candidate_match"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    id_item_enrichment = Column(Uuid, ForeignKey("item_enrichment.id"), nullable=False, index=True)
    id_external_source = Column(Integer, ForeignKey("external_api_source.id"), nullable=False, index=True)
    candidate_doi = Column(String(150), nullable=True)
    match_score = Column(Float, nullable=True)                   # Similitud textual ponderada
    query_result = Column(String(50), nullable=False)            # 'exitosa', 'sin_datos', 'fallida', 'timeout'
    raw_metadata_json = Column(JSON, nullable=True)
    retrieved_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    item_enrichment = relationship("ItemEnrichment", back_populates="candidate_matches")
    external_source = relationship("ExternalAPISource", back_populates="matches")


# =============================================================================
# BITÁCORA DE INFERENCIA DEL LLM (MS2)
# =============================================================================

class LLMClassificationLog(Base):
    """
    Bitácora de inferencia del modelo LLM local (Ollama).
    Dueño: MS2 (Clasificación Área OCDE / ODS)
    """
    __tablename__ = "llm_classification_log"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    id_item_enrichment = Column(Uuid, ForeignKey("item_enrichment.id"), nullable=False, index=True)
    classification_type = Column(String(20), nullable=False, index=True) # 'OCDE' / 'ODS'
    model_version = Column(String(100), nullable=False)          # llama3.2:3b-instruct-q4_K_M
    prompt_template_version = Column(String(50), nullable=False)
    prompt = Column(Text, nullable=False)
    temperature = Column(Float, default=0.0, nullable=False)
    seed = Column(Integer, nullable=True)
    repetition_number = Column(Integer, default=1, nullable=False)
    result_json = Column(JSON, nullable=True)
    llm_reasoning = Column(Text, nullable=True)
    is_info_sufficient = Column(Boolean, default=True, nullable=False)
    execution_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    item_enrichment = relationship("ItemEnrichment", back_populates="classification_logs")


# =============================================================================
# TRABAJOS ASÍNCRONOS Y REINTENTOS (MS4)
# =============================================================================

class Job(Base):
    """
    Bitácora de ejecuciones asíncronas y reintentos (Exponential Backoff).
    Dueño: MS4 (Conexión e Integración DSpace-CRIS)
    """
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


# =============================================================================
# REGISTRO DE SINCRONIZACIÓN Y EXPORTACIÓN DSPACE (MS4)
# =============================================================================

class DSpaceSyncLog(Base):
    """
    Registro de sincronización, exportaciones masivas y confirmaciones.
    Dueño: MS4 (Conexión e Integración DSpace-CRIS)
    """
    __tablename__ = "dspace_sync_log"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    id_item_enrichment = Column(Uuid, ForeignKey("item_enrichment.id"), nullable=False, index=True)
    http_status_code = Column(Integer, nullable=True)
    sync_type = Column(String(50), nullable=False)               # 'Export_CSV', 'REST_PATCH', 'Verification'
    synced_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    item_enrichment = relationship("ItemEnrichment", back_populates="sync_logs")


# =============================================================================
# USUARIOS, ROLES Y AUDITORÍA INMUTABLE (MS3)
# =============================================================================

class Role(Base):
    """
    Roles del sistema (RBAC).
    Dueño: MS3 (Gestión de Usuarios y Autenticación)
    """
    __tablename__ = "role"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False)       # 'Academico', 'Curador_VRIIC', 'Admin'
    description = Column(String(255), nullable=True)

    users = relationship("User", back_populates="role")


class User(Base):
    """
    Usuarios del sistema autenticados vía OIDC institucional.
    Dueño: MS3 (Gestión de Usuarios y Autenticación)
    """
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
    Bitácora inmutable de curaduría (INSERT-only).
    Dueño: MS3 (Gestión de Usuarios y Autenticación)
    """
    __tablename__ = "audit_log"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    id_user = Column(Uuid, ForeignKey("user.id"), nullable=False, index=True)
    id_item_enrichment = Column(Uuid, ForeignKey("item_enrichment.id"), nullable=False, index=True)
    action = Column(String(50), nullable=False)                  # 'Aprobar', 'Rechazar', 'Editar', 'Invalidar'
    previous_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = relationship("User", back_populates="audit_logs")
    item_enrichment = relationship("ItemEnrichment", back_populates="audit_logs")


# =============================================================================
# MODELOS LEGACY PARA COMPATIBILIDAD TRANSICIONAL
# =============================================================================

class DoiRecord(Base):
    __tablename__ = "doi_records"
    id = Column(Integer, primary_key=True, index=True)
    doi = Column(String, unique=True, index=True, nullable=False)


class DocumentMetadata(Base):
    __tablename__ = "document_metadata"
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, nullable=True)
    resumen = Column(Text, nullable=True)
    palabras_clave = Column(String, nullable=True)
    derechos_acceso = Column(String, nullable=True)
    fuente_financiamiento = Column(String, nullable=True)
    area_oce = Column(String, nullable=True)
    area_ods = Column(String, nullable=True)


class DSpaceMetricsHistory(Base):
    __tablename__ = "dspace_metrics_history"
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
