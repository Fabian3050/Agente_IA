import os
import openpyxl
from sqlalchemy.orm import Session
from app.models.db_models import (
    Status, ProposalStatus,
    ExternalAPISource,
    Category,
    Role
)

AREAS_DIR = os.path.join(os.path.dirname(__file__), "..", "areas")
OCDE_FILE = os.path.join(AREAS_DIR, "Areas_OCDE.xlsx")
ODS_FILE = os.path.join(AREAS_DIR, "Areas_ODS.xlsx")


def seed_statuses(db: Session) -> int:
    """Siembra los 12 estados unívocos del ciclo de vida formal."""
    statuses_data = [
        (ProposalStatus.DETECTADA, "El monitoreo detecta campos vacíos en DSpace-CRIS sin propuesta activa previa."),
        (ProposalStatus.EN_RECUPERACION, "Consultas asíncronas iniciadas a las APIs externas científicas (MS1)."),
        (ProposalStatus.COINCIDENCIA_DUDOSA, "Similitud textual no alcanza el umbral de certidumbre o candidatos ambiguos."),
        (ProposalStatus.EN_CLASIFICACION, "Inferencia semántica en proceso con LLM local Ollama para OCDE y ODS (MS2)."),
        (ProposalStatus.EN_REINTENTO, "Falla temporal de red, timeout o indisponibilidad en fuentes o LLM."),
        (ProposalStatus.EN_REVISION, "Propuesta consolidada y trazable disponible en panel web para curaduría humana."),
        (ProposalStatus.INVALIDADA, "El registro original en DSpace-CRIS fue alterado externamente antes/durante la curaduría."),
        (ProposalStatus.RECHAZADA, "El curador desestimó la propuesta registrando el motivo en auditoría."),
        (ProposalStatus.APROBADA, "El curador aprobó o editó los campos validados de la propuesta."),
        (ProposalStatus.EXPORTADA, "Metadatos aprobados agrupados en lote CSV seguro con cero celdas vacías."),
        (ProposalStatus.CARGADA, "Monitoreo posterior confirma que los valores aprobados se reflejan en DSpace-CRIS."),
        (ProposalStatus.CERRADA, "Propuesta finalizada exitosamente en su ciclo operativo o archivada.")
    ]

    count = 0
    for name, desc in statuses_data:
        existing = db.query(Status).filter(Status.name == name).first()
        if not existing:
            db.add(Status(name=name, description=desc))
            count += 1
    db.commit()
    return count


def seed_external_sources(db: Session) -> int:
    """Siembra el catálogo de fuentes científicas externas configuradas (MS1)."""
    sources_data = [
        ("Crossref", "https://api.crossref.org/works", True),
        ("OpenAlex", "https://api.openalex.org/works", True),
        ("Unpaywall", "https://api.unpaywall.org/v2", True),
        ("Europe PMC", "https://www.ebi.ac.uk/europepmc/webservices/rest/search", True),
        ("Semantic Scholar", "https://api.semanticscholar.org/graph/v1/paper/search", True)
    ]

    count = 0
    for name, base_url, is_active in sources_data:
        existing = db.query(ExternalAPISource).filter(ExternalAPISource.name == name).first()
        if not existing:
            db.add(ExternalAPISource(name=name, base_url=base_url, is_active=is_active))
            count += 1
    db.commit()
    return count


def seed_roles(db: Session) -> int:
    """Siembra los roles institucionales del sistema para RBAC (MS3)."""
    roles_data = [
        ("Academico", "Autor / Investigador con visibilidad de solo lectura sobre sus publicaciones"),
        ("Curador_VRIIC", "Curador institucional con facultades de aprobación, edición y rechazo"),
        ("Admin", "Administrador técnico del sistema con facultades de configuración y exportación")
    ]

    count = 0
    for name, desc in roles_data:
        existing = db.query(Role).filter(Role.name == name).first()
        if not existing:
            db.add(Role(name=name, description=desc))
            count += 1
    db.commit()
    return count


def seed_categories(db: Session) -> int:
    """
    Siembra el catálogo estandarizado oficial (FORD OCDE 2007 y ODS ONU 2015).
    Dueño: MS2.
    """
    count = 0

    # 1. Cargar FORD OCDE
    if os.path.exists(OCDE_FILE):
        wb = openpyxl.load_workbook(OCDE_FILE)
        sheet = wb.active
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if not row or not row[0]:
                continue
            
            # Si hay disciplina específica (columna 4 y 5)
            cod_disc = str(row[4]).strip() if len(row) > 4 and row[4] else None
            nom_disc = str(row[5]).strip() if len(row) > 5 and row[5] else None
            nom_subarea = str(row[3]).strip() if len(row) > 3 and row[3] else None
            nom_area = str(row[1]).strip() if len(row) > 1 and row[1] else None

            code = cod_disc or (str(row[2]).strip() if len(row) > 2 and row[2] else str(row[0]).strip())
            name = nom_disc or nom_subarea or nom_area
            desc = f"Área: {nom_area} | Subárea: {nom_subarea}" if nom_subarea else f"Área: {nom_area}"

            existing = db.query(Category).filter(
                Category.code == code,
                Category.scheme == "OCDE"
            ).first()

            if not existing and code and name:
                db.add(Category(
                    code=code,
                    name=name,
                    scheme="OCDE",
                    version="2007",
                    description=desc
                ))
                count += 1

    # 2. Cargar ODS ONU
    if os.path.exists(ODS_FILE):
        wb = openpyxl.load_workbook(ODS_FILE)
        sheet = wb.active
        for row in sheet.iter_rows(min_row=5, values_only=True):
            if not row or not row[0] or not row[1]:
                continue
            try:
                cod_int = int(float(row[0]))
                code = f"ODS {cod_int}"
                name = str(row[1]).strip()
                desc = str(row[2]).strip() if len(row) > 2 and row[2] else ""

                existing = db.query(Category).filter(
                    Category.code == code,
                    Category.scheme == "ODS"
                ).first()

                if not existing:
                    db.add(Category(
                        code=code,
                        name=name,
                        scheme="ODS",
                        version="2015",
                        description=desc
                    ))
                    count += 1
            except (ValueError, TypeError):
                continue

    db.commit()
    return count


def run_full_seeding(db: Session) -> dict:
    """Ejecuta el seeding completo de catálogos parametrizados oficiales."""
    s_count = seed_statuses(db)
    src_count = seed_external_sources(db)
    r_count = seed_roles(db)
    c_count = seed_categories(db)
    return {
        "statuses_created": s_count,
        "external_sources_created": src_count,
        "roles_created": r_count,
        "categories_created": c_count
    }

