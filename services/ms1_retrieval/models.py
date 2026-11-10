import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, Float, Boolean, JSON, DateTime, ForeignKey, Uuid
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

from common.database import Base


# =============================================================================
# MODELOS SQLALCHEMY PROPIETARIOS DE MS1
# =============================================================================

class ExternalAPISource(Base):
    __tablename__ = "external_api_source"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    base_url = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    matches = relationship("CandidateMatch", back_populates="external_source")


class CandidateMatch(Base):
    __tablename__ = "candidate_match"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    id_item_enrichment = Column(Uuid, nullable=False, index=True)
    id_external_source = Column(Integer, ForeignKey("external_api_source.id"), nullable=False, index=True)
    candidate_doi = Column(String(150), nullable=True)
    match_score = Column(Float, nullable=True)
    query_result = Column(String(50), nullable=False)  # 'exitosa', 'sin_datos', 'fallida', 'timeout'
    raw_metadata_json = Column(JSON, nullable=True)
    retrieved_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    external_source = relationship("ExternalAPISource", back_populates="matches")


# =============================================================================
# ESQUEMAS PYDANTIC (DTOs)
# =============================================================================

class RetrievalRequest(BaseModel):
    item_id: uuid.UUID = Field(description="UUID del ItemEnrichment en MS4")
    doi: Optional[str] = Field(default=None, description="DOI registrado si existe")
    title: Optional[str] = Field(default=None, description="Título del documento")
    author: Optional[str] = Field(default=None, description="Primer autor")
    year: Optional[int] = Field(default=None, description="Año de publicación")


class CandidateMetadataDTO(BaseModel):
    title: str
    authors: List[str] = []
    doi: Optional[str] = None
    year: Optional[int] = None
    source: str
    url: Optional[str] = None
    abstract: Optional[str] = None
    keywords: Optional[List[str]] = None
    author_keywords: Optional[List[str]] = None
    automated_concepts: Optional[List[str]] = None
    funding_source: Optional[List[str]] = None
    funding_agency: Optional[str] = None
    funding_id: Optional[str] = None
    funding_grant_number: Optional[str] = None
    oa_status: Optional[str] = None
    license: Optional[str] = None
    version_type: Optional[str] = None


class RetrievalResponse(BaseModel):
    outcome: str  # 'ALTA_COINCIDENCIA', 'COINCIDENCIA_DUDOSA', 'SIN_DATOS', 'DESCARTADA'
    max_score: float
    best_source: Optional[str] = None
    consolidated: Dict[str, Any]
    query_statuses: Dict[str, str]

