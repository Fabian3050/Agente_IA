from sqlalchemy import Column, Integer, String, Text
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
