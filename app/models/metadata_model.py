from pydantic import BaseModel
from typing import List, Optional

class MetadataResponse(BaseModel):
    title: str
    authors: List[str] = []
    doi: Optional[str] = None
    year: Optional[int] = None
    source: str  # 'crossref', 'openalex', 'semanticscholar', 'europepmc', 'unpaywall'
    url: Optional[str] = None
    abstract: Optional[str] = None
    keywords: Optional[List[str]] = None
    author_keywords: Optional[List[str]] = None      # dc.subject
    automated_concepts: Optional[List[str]] = None   # cris.concept
    s2FieldsOfStudy: Optional[list] = None
    funding_source: Optional[List[str]] = None
    funding_agency: Optional[str] = None
    funding_id: Optional[str] = None
    funding_grant_number: Optional[str] = None
    ods: Optional[List[str]] = None
    derechos_acceso: Optional[str] = None            # Legacy
    oa_status: Optional[str] = None                  # Gold, Green, Bronze, Hybrid, Closed
    license: Optional[str] = None                    # ej. CC-BY
    version_type: Optional[str] = None               # Preprint, Postprint, PublishedVersion
