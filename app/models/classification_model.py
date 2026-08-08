from pydantic import BaseModel
from typing import Optional, List
from app.models.metadata_model import MetadataResponse

class OCDEClassificationItem(BaseModel):
    codigo_ocde: str
    area_ocde: str
    justificacion: str

class OCDEClassificationResponse(BaseModel):
    clasificaciones: List[OCDEClassificationItem]
    articulo: MetadataResponse

class ODSClassificationItem(BaseModel):
    numero_ods: str
    nombre_ods: str
    justificacion: str

class ODSClassificationResponse(BaseModel):
    clasificaciones: List[ODSClassificationItem]
    articulo: MetadataResponse
