import os
from sqlalchemy.orm import Session
from models import Status, ProposalStatus


def seed_statuses(db: Session) -> int:
    """Siembra los 12 estados unívocos del ciclo de vida formal en MS4."""
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


def run_full_seeding(db: Session) -> dict:
    s_count = seed_statuses(db)
    return {
        "statuses_created": s_count
    }
