import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, Float, Boolean, JSON, Text, DateTime, Uuid
from pydantic import BaseModel, Field

from common.database import Base


# =============================================================================
# MODELOS SQLALCHEMY PROPIETARIOS DE MS2
# =============================================================================

class Category(Base):
    __tablename__ = "category"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), nullable=False, index=True)        # ej. 1.1, ODS 7
    name = Column(String(255), nullable=False)
    scheme = Column(String(20), nullable=False, index=True)      # 'OCDE' / 'ODS'
    version = Column(String(20), nullable=False)                 # '2007' / '2015'
    description = Column(Text, nullable=True)


class LLMClassificationLog(Base):
    __tablename__ = "llm_classification_log"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    id_item_enrichment = Column(Uuid, nullable=False, index=True)
    classification_type = Column(String(20), nullable=False, index=True) # 'OCDE' / 'ODS'
    model_version = Column(String(100), nullable=False)
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


# =============================================================================
# ESQUEMAS PYDANTIC (DTOs)
# =============================================================================

class ClassificationRequest(BaseModel):
    item_id: uuid.UUID = Field(description="UUID del ItemEnrichment en MS4")
    title: Optional[str] = Field(default=None)
    abstract: Optional[str] = Field(default=None)
    keywords: Optional[str] = Field(default=None)
    temperature: float = Field(default=0.0)
    repetition_number: int = Field(default=1)


class OCDEItemDTO(BaseModel):
    codigo_area: str
    nombre_area: str
    codigo_subarea: str = ""
    nombre_subarea: str = ""
    codigo_disciplina: str
    nombre_disciplina: str
    justificacion: str
    confidence_score: float = 0.95


class ODSItemDTO(BaseModel):
    numero_ods: str
    nombre_ods: str
    justificacion: str
    confidence_score: float = 0.95


class ClassificationResultResponse(BaseModel):
    is_info_sufficient: bool
    ocde_categories: List[OCDEItemDTO]
    ods_categories: List[ODSItemDTO]
    ocde_reasoning: Optional[str] = None
    ods_reasoning: Optional[str] = None
    execution_time_total_ms: int

