from pydantic import BaseModel, Field
from typing import Optional, List
from app.models.metadata_model import MetadataResponse

# ---------------------------------------------------------------------------
# MODELOS PYDANTIC PARA CLASIFICACIÓN FORD OCDE (MS2)
# ---------------------------------------------------------------------------

class OCDEClassificationItem(BaseModel):
    codigo_area: str = Field(description="Código del área OCDE (ej: 1, 2)")
    nombre_area: str = Field(description="Nombre del gran área OCDE")
    codigo_subarea: str = Field(default="", description="Código de la subárea (ej: 1.1)")
    nombre_subarea: str = Field(default="", description="Nombre de la subárea")
    codigo_disciplina: str = Field(description="Código exacto de la disciplina FORD (ej: 1.1.1 o 2.7)")
    nombre_disciplina: str = Field(description="Nombre oficial de la disciplina")
    justificacion: str = Field(description="Justificación metodológica y temática de la asignación")
    confidence_score: Optional[float] = Field(default=0.9, ge=0.0, le=1.0)


class OCDEClassificationResult(BaseModel):
    """Estructura esperada directamente del JSON del LLM"""
    clasificaciones: List[OCDEClassificationItem] = Field(default_factory=list, max_length=2)
    is_info_sufficient: bool = Field(default=True, description="False si el resumen es insuficiente o ambiguo")
    razonamiento_global: Optional[str] = Field(default=None, description="Razonamiento general del modelo")


class OCDEClassificationResponse(BaseModel):
    """Respuesta consolidada para endpoints de API y servicios"""
    clasificaciones: List[OCDEClassificationItem] = Field(default_factory=list, max_length=2)
    is_info_sufficient: bool = True
    razonamiento_global: Optional[str] = None
    articulo: Optional[MetadataResponse] = None


# ---------------------------------------------------------------------------
# MODELOS PYDANTIC PARA CLASIFICACIÓN ODS ONU (MS2)
# ---------------------------------------------------------------------------

class ODSClassificationItem(BaseModel):
    numero_ods: str = Field(description="Número del ODS (1 al 17)")
    nombre_ods: str = Field(description="Nombre oficial del Objetivo de Desarrollo Sostenible")
    justificacion: str = Field(description="Justificación del impacto socioeconómico o ambiental reportado")
    confidence_score: Optional[float] = Field(default=0.9, ge=0.0, le=1.0)


class ODSClassificationResult(BaseModel):
    """Estructura esperada directamente del JSON del LLM"""
    clasificaciones: List[ODSClassificationItem] = Field(default_factory=list, max_length=2)
    is_info_sufficient: bool = Field(default=True, description="False si el resumen es insuficiente o ambiguo")
    razonamiento_global: Optional[str] = Field(default=None, description="Razonamiento general del modelo")


class ODSClassificationResponse(BaseModel):
    """Respuesta consolidada para endpoints de API y servicios"""
    clasificaciones: List[ODSClassificationItem] = Field(default_factory=list, max_length=2)
    is_info_sufficient: bool = True
    razonamiento_global: Optional[str] = None
    articulo: Optional[MetadataResponse] = None
