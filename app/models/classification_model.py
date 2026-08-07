from pydantic import BaseModel
from typing import Optional, List
from app.models.metadata_model import MetadataResponse

class OCDEClassificationResponse(BaseModel):
    codigo_ocde: str
    area_ocde: str
    justificacion: str
    articulo: MetadataResponse
