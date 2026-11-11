import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from common.database import get_db
from models import (
    ItemEnrichment, Status, ProposalStatus, FieldProposal, ItemCategory,
    Job, DSpaceSyncLog
)
from services.orchestrator_service import MS4Orchestrator as DSpaceOrchestratorServiceMS4

router = APIRouter(
    prefix="/v3/proposals",
    tags=["V3 Proposals & Curation"]
)

orchestrator = DSpaceOrchestratorServiceMS4()


class CurationDecisionRequest(BaseModel):
    user_id: uuid.UUID = Field(description="UUID del usuario curador")
    decision: str = Field(description="'Aprobar', 'Rechazar' o 'Editar'")
    edited_fields: Optional[Dict[str, str]] = Field(default=None, description="Diccionario {campo: nuevo_valor}")
    rejection_reason: Optional[str] = Field(default=None, description="Motivo en caso de rechazo")
    dspace_live_last_modified: Optional[datetime] = Field(default=None, description="Timestamp actual de DSpace para verificar concurrencia")


@router.get("/")
def list_proposals(
    status_filter: Optional[str] = Query(None, description="Filtrar por nombre de estado formal"),
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lista las propuestas de enriquecimiento con filtrado por estado y paginación."""
    query = db.query(ItemEnrichment)
    if status_filter:
        query = query.join(Status).filter(Status.name == status_filter)

    total = query.count()
    items = query.order_by(ItemEnrichment.created_at.desc()).offset(page * size).limit(size).all()

    return {
        "total": total,
        "page": page,
        "size": size,
        "items": [
            {
                "id": str(i.id),
                "uuid_dspace": i.uuid_dspace,
                "doi": i.doi,
                "title": i.title,
                "status": i.status.name if i.status else None,
                "oa_status": i.oa_status,
                "created_at": i.created_at.isoformat() if i.created_at else None,
                "updated_at": i.updated_at.isoformat() if i.updated_at else None
            }
            for i in items
        ]
    }


@router.get("/{item_id}")
def get_proposal_detail(item_id: uuid.UUID, db: Session = Depends(get_db)):
    """Obtiene el detalle atómico completo de una propuesta, su proveniencia y asignaciones."""
    item = db.query(ItemEnrichment).filter(ItemEnrichment.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Propuesta no encontrada")

    # Campos propuestos atómicos
    proposals = [
        {
            "id": str(p.id),
            "field_name": p.field_name,
            "original_dspace_value": p.original_dspace_value,
            "proposed_value": p.proposed_value,
            "source": p.source,
            "rule_applied": p.rule_applied,
            "final_value": p.final_value,
            "is_edited_by_curator": p.is_edited_by_curator,
            "retrieved_at": p.retrieved_at.isoformat() if p.retrieved_at else None
        }
        for p in item.field_proposals
    ]

    # Categorías asignadas
    categories = [
        {
            "scheme": c.category.scheme if c.category else None,
            "code": c.category.code if c.category else None,
            "name": c.category.name if c.category else None,
            "origin": c.origin,
            "priority_order": c.priority_order,
            "confidence_score": c.confidence_score
        }
        for c in item.categories
    ]

    # Auditoría
    audit = [
        {
            "id": str(a.id),
            "action": a.action,
            "rejection_reason": a.rejection_reason,
            "timestamp": a.timestamp.isoformat() if a.timestamp else None
        }
        for a in item.audit_logs
    ]

    return {
        "id": str(item.id),
        "uuid_dspace": item.uuid_dspace,
        "doi": item.doi,
        "title": item.title,
        "abstract": item.abstract,
        "author_keywords": item.author_keywords,
        "automated_concepts": item.automated_concepts,
        "oa_status": item.oa_status,
        "license": item.license,
        "version_type": item.version_type,
        "funding_agency": item.funding_agency,
        "funding_id": item.funding_id,
        "funding_grant_number": item.funding_grant_number,
        "status": item.status.name if item.status else None,
        "last_modified_dspace": item.last_modified_dspace.isoformat() if item.last_modified_dspace else None,
        "proposals": proposals,
        "categories": categories,
        "audit_logs": audit
    }


@router.post("/{item_id}/curate")
def curate_proposal(
    item_id: uuid.UUID,
    payload: CurationDecisionRequest,
    db: Session = Depends(get_db)
):
    """Aplica la decisión del curador humano con revalidación de concurrencia y bitácora inmutable."""
    item = db.query(ItemEnrichment).filter(ItemEnrichment.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Propuesta no encontrada")

    res = orchestrator.apply_curator_decision(
        db=db,
        item=item,
        user_id=payload.user_id,
        decision=payload.decision,
        edited_fields=payload.edited_fields,
        rejection_reason=payload.rejection_reason,
        dspace_live_last_modified=payload.dspace_live_last_modified
    )
    return res


@router.post("/export-csv")
def export_approved_proposals(db: Session = Depends(get_db)):
    """
    Genera lotes CSV estructurados para DSpace con CERO celdas vacías
    según el protocolo de exportación segura de la Sección 1.4.
    """
    batches = orchestrator.export_approved_proposals_csv(db)
    return {
        "status": "success",
        "total_batches": len(batches),
        "batches": batches
    }

