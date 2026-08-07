from pydantic import BaseModel
from typing import List, Optional

class MetadataResponse(BaseModel):
    title: str
    authors: List[str]
    doi: Optional[str] = None
    year: Optional[int] = None
    source: str  # e.g., 'crossref', 'openalex', 'semanticscholar', 'europepmc'
    url: Optional[str] = None
    abstract: Optional[str] = None
    keywords: Optional[List[str]] = None
    s2FieldsOfStudy: Optional[list] = None
    funding_source: Optional[List[str]] = None
    ods: Optional[List[str]] = None
