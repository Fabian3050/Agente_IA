from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from datetime import datetime
from app.database import Base

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
    """
    Histórico de auditoría y métricas globales de DSpace.
    Permite visualizar en dashboards la evolución temporal de los registros incompletos.
    """
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
    """
    Cola de enriquecimiento individual de publicaciones de DSpace.
    Rastrea el estado y los metadatos recuperados desde fuentes académicas externas y LLM (Ollama).
    """
    __tablename__ = "dspace_enrichment_queue"

    id = Column(Integer, primary_key=True, index=True)
    dspace_uuid = Column(String, unique=True, index=True, nullable=False)
    doi = Column(String, index=True, nullable=True)
    titulo = Column(Text, nullable=True)
    tipo_recurso = Column(String, nullable=True)
    tipo_falencia = Column(String, nullable=True)  # SIN_ABSTRACT_CON_DOI, SIN_DOI_NI_ABSTRACT, etc.
    estado = Column(String, index=True, default="PENDIENTE")  # PENDIENTE, ENRIQUECIDO_FUENTES, CLASIFICADO_LLM, COMPLETO, ERROR, NO_ENCONTRADO, SINCRONIZADO_DSPACE
    
    # Metadatos enriquecidos desde fuentes académicas (OpenAlex, CrossRef, Europe PMC, etc.)
    fuente_enriquecimiento = Column(String, nullable=True)  # openalex, crossref, etc.
    abstract_enriquecido = Column(Text, nullable=True)
    palabras_clave = Column(JSON, nullable=True)
    fuente_financiamiento = Column(JSON, nullable=True)
    derechos_acceso = Column(String, nullable=True)
    
    # Clasificaciones temáticas generadas por IA (LLM vía Ollama)
    area_ocde = Column(JSON, nullable=True)
    area_ods = Column(JSON, nullable=True)
    
    # Respaldo de metadatos completos y estado de ejecución
    metadatos_recuperados = Column(JSON, nullable=True)  # Metadata JSON cruda de respaldo
    resumen_original = Column(Text, nullable=True)
    intentos = Column(Integer, default=0)
    mensaje_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
