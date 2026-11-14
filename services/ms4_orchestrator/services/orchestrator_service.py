import csv
import io
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Callable
from collections import defaultdict
from sqlalchemy.orm import Session

try:
    from models import (
        ItemEnrichment, Status, ProposalStatus,
        FieldProposal, ItemCategory,
        Job, DSpaceSyncLog
    )
except ImportError:
    from services.ms4_orchestrator.models import (
        ItemEnrichment, Status, ProposalStatus,
        FieldProposal, ItemCategory,
        Job, DSpaceSyncLog
    )

try:
    from clients.ms_clients import MS1Client, MS2Client, MS3Client
except ImportError:
    from services.ms4_orchestrator.clients.ms_clients import MS1Client, MS2Client, MS3Client

try:
    from common.messaging import publish_event
except ImportError:
    from services.common.messaging import publish_event

logger = logging.getLogger(__name__)


class MS4Orchestrator:
    """
    Microservicio 4: Orquestación del ciclo de vida (12 estados),
    idempotencia temprana, proveniencia atómica, concurrencia y exportación CSV segura en 2 pasos.
    Escribe exclusivamente en Item_Enrichment, Field_Proposal, Item_Category, Status, Job y DSpace_Sync_Log.
    """

    def __init__(self):
        self.ms1 = MS1Client()
        self.ms2 = MS2Client()
        self.ms3 = MS3Client()

    def get_status_by_name(self, db: Session, name: str) -> Status:
        st = db.query(Status).filter(Status.name == name).first()
        if not st:
            st = Status(name=name, description=f"Estado {name}")
            db.add(st)
            db.commit()
            db.refresh(st)
        return st

    # -------------------------------------------------------------------------
    # 1. IDEMPOTENCIA TEMPRANA Y DETECCIÓN
    # -------------------------------------------------------------------------
    def handle_detection(
        self,
        db: Session,
        uuid_dspace: str,
        doi: Optional[str] = None,
        title: Optional[str] = None,
        last_modified_dspace: Optional[datetime] = None,
        force_reprocess: bool = False
    ) -> Tuple[Optional[ItemEnrichment], str]:
        existing = db.query(ItemEnrichment).filter(ItemEnrichment.uuid_dspace == uuid_dspace).first()

        if existing:
            st_name = existing.status.name if existing.status else ""
            omitted = [
                ProposalStatus.EN_REVISION, ProposalStatus.APROBADA,
                ProposalStatus.EXPORTADA, ProposalStatus.CARGADA,
                ProposalStatus.CERRADA, ProposalStatus.EN_RECUPERACION,
                ProposalStatus.EN_CLASIFICACION, ProposalStatus.EN_REINTENTO
            ]
            if st_name in omitted:
                return None, f"OMITIDO_IDEMPOTENCIA: Ítem {uuid_dspace} en estado activo '{st_name}'"

            if st_name == ProposalStatus.INVALIDADA:
                if last_modified_dspace and existing.last_modified_dspace != last_modified_dspace:
                    existing.last_modified_dspace = last_modified_dspace
                    existing.status = self.get_status_by_name(db, ProposalStatus.DETECTADA)
                    db.commit()
                    return existing, "REABIERTA_POR_CAMBIO_DSPACE"
                return None, "OMITIDO: Invalidada sin cambios"

            if st_name == ProposalStatus.RECHAZADA:
                if force_reprocess:
                    existing.status = self.get_status_by_name(db, ProposalStatus.DETECTADA)
                    db.commit()
                    return existing, "REPROCESO_HABILITADO"
                return None, "OMITIDO: Rechazada por curador"

        # Crear nuevo registro en Detectada
        st_det = self.get_status_by_name(db, ProposalStatus.DETECTADA)
        new_item = ItemEnrichment(
            uuid_dspace=uuid_dspace,
            doi=doi,
            title=title,
            last_modified_dspace=last_modified_dspace,
            id_status=st_det.id
        )
        db.add(new_item)
        db.commit()
        db.refresh(new_item)

        # Transitar a En_recuperacion
        new_item.status = self.get_status_by_name(db, ProposalStatus.EN_RECUPERACION)
        db.commit()
        return new_item, "CREADA_Y_EN_RECUPERACION"

    # Alias para compatibilidad
    handle_detected_item = handle_detection

    # -------------------------------------------------------------------------
    # 2. COMUNICACIÓN ASÍNCRONA VIA RABBITMQ (MS4 -> MS1)
    # -------------------------------------------------------------------------
    def dispatch_retrieval_async(self, db: Session, item: ItemEnrichment) -> bool:
        """
        Publica una solicitud de recuperación a RabbitMQ ('dspace.retrieval.requests').
        Transita el ítem a En_recuperacion y registra el Job en progreso.
        """
        item.status = self.get_status_by_name(db, ProposalStatus.EN_RECUPERACION)
        job = Job(id_item_enrichment=item.id, stage="Recuperacion", status="En_Progreso")
        db.add(job)
        db.commit()

        payload = {
            "item_id": str(item.id),
            "uuid_dspace": item.uuid_dspace,
            "doi": item.doi,
            "title": item.title,
            "reply_queue": "dspace.retrieval.responses"
        }
        published = publish_event("dspace.retrieval.requests", payload)
        if not published:
            logger.warning(f"No se pudo despachar por RabbitMQ para item {item.id}, fallback a sincrono.")
        return published

    def handle_retrieval_response(self, db: Session, payload: Dict[str, Any]) -> None:
        """
        Procesa la respuesta asíncrona de MS1 recibida desde RabbitMQ ('dspace.retrieval.responses').
        Actualiza el ítem, crea FieldProposals y transita a En_clasificacion o En_revision/En_reintento.
        """
        item_id_raw = payload.get("item_id")
        if not item_id_raw:
            return

        item_id = uuid.UUID(item_id_raw) if isinstance(item_id_raw, str) else item_id_raw
        item = db.query(ItemEnrichment).filter(ItemEnrichment.id == item_id).first()
        if not item:
            logger.warning(f"[MS4] Ítem {item_id} no encontrado para respuesta de recuperación.")
            return

        job = db.query(Job).filter(
            Job.id_item_enrichment == item.id,
            Job.stage == "Recuperacion"
        ).order_by(Job.created_at.desc()).first()

        outcome = payload.get("outcome")
        consolidated = payload.get("consolidated") or {}

        if outcome == "COINCIDENCIA_DUDOSA":
            item.status = self.get_status_by_name(db, ProposalStatus.COINCIDENCIA_DUDOSA)
            if job:
                job.status = "Completado"
                job.last_error = "Coincidencia dudosa: derivar a curador"
            db.commit()
            item.status = self.get_status_by_name(db, ProposalStatus.EN_REVISION)
            db.commit()
            return

        if outcome in ["DESCARTADA", "SIN_DATOS", "ERROR"]:
            if job:
                job.status = "Fallido"
                job.retry_count += 1
                job.last_error = payload.get("error", f"Resultado {outcome}")
            if job and job.retry_count < 3:
                item.status = self.get_status_by_name(db, ProposalStatus.EN_REINTENTO)
            else:
                item.status = self.get_status_by_name(db, ProposalStatus.EN_REVISION)
            db.commit()
            return

        # Consolidación exitosa
        self._apply_consolidated_metadata(db, item, consolidated)
        if job:
            job.status = "Completado"
        item.status = self.get_status_by_name(db, ProposalStatus.EN_CLASIFICACION)
        db.commit()

    def _apply_consolidated_metadata(self, db: Session, item: ItemEnrichment, consolidated: Dict[str, Any]):
        if consolidated.get("doi"): item.doi = consolidated["doi"]
        if consolidated.get("abstract"): item.abstract = consolidated["abstract"]
        if consolidated.get("author_keywords"): item.author_keywords = consolidated["author_keywords"]
        if consolidated.get("automated_concepts"): item.automated_concepts = consolidated["automated_concepts"]
        if consolidated.get("funding_agency"): item.funding_agency = consolidated["funding_agency"]
        if consolidated.get("funding_id"): item.funding_id = consolidated["funding_id"]
        if consolidated.get("funding_grant_number"): item.funding_grant_number = consolidated["funding_grant_number"]
        if consolidated.get("oa_status"): item.oa_status = consolidated["oa_status"]
        if consolidated.get("license"): item.license = consolidated["license"]
        if consolidated.get("version_type"): item.version_type = consolidated["version_type"]

        fields_to_save = [
            ("dc.description.abstract", consolidated.get("abstract"), consolidated.get("abstract_source"), "prioridad_abstract"),
            ("dc.subject", consolidated.get("author_keywords"), "Fuentes combinadas", "palabras_clave_autor"),
            ("cris.concept", consolidated.get("automated_concepts"), "OpenAlex", "conceptos_algoritmicos"),
            ("funding_agency", consolidated.get("funding_agency"), "Crossref/OpenAlex", "desglose_financiamiento"),
            ("oa_status", consolidated.get("oa_status"), "Unpaywall", "open_access_estandar"),
            ("version_type", consolidated.get("version_type"), "OpenAlex/Unpaywall", "version_manuscrito")
        ]
        for f_name, val, src, rule in fields_to_save:
            if val:
                db.add(FieldProposal(
                    id_item_enrichment=item.id,
                    field_name=f_name,
                    proposed_value=str(val),
                    source=src,
                    rule_applied=rule,
                    final_value=str(val)
                ))
        db.commit()

    # -------------------------------------------------------------------------
    # 3. PIPELINE COMPLETO SINCRONO / ORQUESTADO
    # -------------------------------------------------------------------------
    async def run_pipeline_for_item(self, db: Session, item: ItemEnrichment) -> Dict[str, Any]:
        """Coordina la ejecución de MS1 y MS2 para una publicación."""
        job = Job(id_item_enrichment=item.id, stage="Recuperacion", status="En_Progreso")
        db.add(job)
        db.commit()

        # 1. Llamar a MS1 (Recuperación)
        try:
            res_ms1 = await self.ms1.retrieve(item_id=item.id, doi=item.doi, title=item.title)
            outcome = res_ms1.get("outcome")
            consolidated = res_ms1.get("consolidated", {})

            if outcome == "COINCIDENCIA_DUDOSA":
                item.status = self.get_status_by_name(db, ProposalStatus.COINCIDENCIA_DUDOSA)
                job.status = "Completado"
                job.last_error = "Coincidencia dudosa: derivar a curador"
                db.commit()
                item.status = self.get_status_by_name(db, ProposalStatus.EN_REVISION)
                db.commit()
                return {"status": "COINCIDENCIA_DUDOSA"}

            if outcome in ["DESCARTADA", "SIN_DATOS"]:
                job.status = "Fallido"
                item.status = self.get_status_by_name(db, ProposalStatus.EN_REVISION)
                db.commit()
                return {"status": outcome}

            self._apply_consolidated_metadata(db, item, consolidated)
            job.status = "Completado"
            item.status = self.get_status_by_name(db, ProposalStatus.EN_CLASIFICACION)
            db.commit()

        except Exception as e:
            job.status = "Fallido"
            job.retry_count += 1
            job.last_error = str(e)
            item.status = self.get_status_by_name(db, ProposalStatus.EN_REINTENTO if job.retry_count < 3 else ProposalStatus.EN_REVISION)
            db.commit()
            return {"status": "ERROR_MS1", "error": str(e)}

        # 2. Llamar a MS2 (Clasificación)
        job_cls = Job(id_item_enrichment=item.id, stage="Clasificacion", status="En_Progreso")
        db.add(job_cls)
        db.commit()

        try:
            res_ms2 = await self.ms2.classify(
                item_id=item.id,
                title=item.title,
                abstract=item.abstract,
                keywords=item.author_keywords
            )
            # Guardar categorías en ItemCategory
            for idx, c in enumerate(res_ms2.get("ocde_categories", [])[:2], start=1):
                db.add(ItemCategory(
                    id_item_enrichment=item.id,
                    id_category=1,
                    origin="LLM",
                    priority_order=idx,
                    confidence_score=c.get("confidence_score", 0.95)
                ))
            for idx, c in enumerate(res_ms2.get("ods_categories", [])[:2], start=1):
                db.add(ItemCategory(
                    id_item_enrichment=item.id,
                    id_category=2,
                    origin="LLM",
                    priority_order=idx,
                    confidence_score=c.get("confidence_score", 0.95)
                ))

            job_cls.status = "Completado"
            item.status = self.get_status_by_name(db, ProposalStatus.EN_REVISION)
            db.commit()
            return {"status": "EN_REVISION"}

        except Exception as e:
            job_cls.status = "Fallido"
            job_cls.retry_count += 1
            job_cls.last_error = str(e)
            item.status = self.get_status_by_name(db, ProposalStatus.EN_REINTENTO if job_cls.retry_count < 3 else ProposalStatus.EN_REVISION)
            db.commit()
            return {"status": "ERROR_MS2", "error": str(e)}

    # -------------------------------------------------------------------------
    # 4. CURADURÍA HUMANA Y REVALIDACIÓN DE CONCURRENCIA
    # -------------------------------------------------------------------------
    async def apply_curation(
        self,
        db: Session,
        item: ItemEnrichment,
        user_id: uuid.UUID,
        decision: str,
        edited_fields: Optional[Dict[str, str]] = None,
        rejection_reason: Optional[str] = None,
        dspace_live_last_modified: Optional[datetime] = None
    ) -> Dict[str, Any]:
        # Revalidar concurrencia: ¿Cambió en DSpace?
        if dspace_live_last_modified and item.last_modified_dspace:
            if dspace_live_last_modified != item.last_modified_dspace:
                item.status = self.get_status_by_name(db, ProposalStatus.INVALIDADA)
                await self.ms3.record_audit(
                    user_id=user_id,
                    item_id=item.id,
                    action="Invalidar",
                    rejection_reason="Registro modificado en DSpace antes de finalizar curaduría."
                )
                db.commit()
                return {"result": "INVALIDADA", "message": "Registro invalidado por modificación en DSpace."}

        prev_data = {"abstract": item.abstract, "keywords": item.author_keywords, "funding": item.funding_agency}

        if decision == "Rechazar":
            item.status = self.get_status_by_name(db, ProposalStatus.RECHAZADA)
            await self.ms3.record_audit(
                user_id=user_id,
                item_id=item.id,
                action="Rechazar",
                previous_value=prev_data,
                rejection_reason=rejection_reason
            )
            db.commit()
            return {"result": "RECHAZADA"}

        # Aprobar / Editar
        if edited_fields:
            for f_name, new_val in edited_fields.items():
                fp = db.query(FieldProposal).filter(
                    FieldProposal.id_item_enrichment == item.id,
                    FieldProposal.field_name == f_name
                ).first()
                if fp:
                    fp.final_value = new_val
                    fp.is_edited_by_curator = True
                if f_name == "dc.description.abstract": item.abstract = new_val
                elif f_name == "dc.subject": item.author_keywords = new_val

        item.status = self.get_status_by_name(db, ProposalStatus.APROBADA)
        new_data = {"abstract": item.abstract, "keywords": item.author_keywords, "funding": item.funding_agency}
        await self.ms3.record_audit(
            user_id=user_id,
            item_id=item.id,
            action="Editar" if edited_fields else "Aprobar",
            previous_value=prev_data,
            new_value=new_data
        )
        db.commit()
        return {"result": "APROBADA"}

    # Alias para compatibilidad
    apply_curator_decision = apply_curation

    # -------------------------------------------------------------------------
    # 5. EXPORTACIÓN CSV EN DOS PASOS Y AGRUPACIÓN POR SUBCONJUNTO (CERO CELDAS VACÍAS)
    # -------------------------------------------------------------------------
    def export_csv_zero_empty_cells(
        self,
        db: Session,
        dspace_live_checker: Optional[Callable[[str], Optional[datetime]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Exportación en 2 pasos:
        Paso 1: Revalida la fecha de modificación (last_modified_dspace) con DSpace-CRIS en vivo.
                Si difiere, transita a 'Invalidada' y se excluye del lote.
        Paso 2: Agrupa las propuestas válidas en archivos CSV independientes por subconjunto exacto
                de columnas con valor, garantizando CERO celdas vacías para no borrar metadatos existentes.
        Transita las exportadas a 'Exportada' y registra DSpaceSyncLog.
        """
        st_aprobada = self.get_status_by_name(db, ProposalStatus.APROBADA)
        st_exportada = self.get_status_by_name(db, ProposalStatus.EXPORTADA)
        st_invalidada = self.get_status_by_name(db, ProposalStatus.INVALIDADA)

        items = db.query(ItemEnrichment).filter(ItemEnrichment.id_status == st_aprobada.id).all()
        if not items:
            return []

        # Paso 1: Revalidación en vivo
        valid_items: List[ItemEnrichment] = []
        for it in items:
            if dspace_live_checker:
                live_modified = dspace_live_checker(it.uuid_dspace)
                if live_modified and it.last_modified_dspace and live_modified != it.last_modified_dspace:
                    it.status = st_invalidada
                    db.add(DSpaceSyncLog(
                        id_item_enrichment=it.id,
                        sync_type="Invalidated_External_Change",
                        http_status_code=409
                    ))
                    db.commit()
                    continue
            valid_items.append(it)

        if not valid_items:
            return []

        # Paso 2: Agrupación por subconjunto exacto de columnas para garantizar CERO celdas vacías
        batches = defaultdict(list)
        for it in valid_items:
            row = {"id": it.uuid_dspace}
            if it.abstract and it.abstract.strip(): row["dc.description.abstract"] = it.abstract.strip()
            if it.author_keywords and it.author_keywords.strip(): row["dc.subject"] = it.author_keywords.strip()
            if it.automated_concepts and it.automated_concepts.strip(): row["cris.concept"] = it.automated_concepts.strip()
            if it.funding_agency and it.funding_agency.strip(): row["dc.description.sponsorship"] = it.funding_agency.strip()
            if it.oa_status and it.oa_status.strip(): row["dc.rights.accessRights"] = it.oa_status.strip()

            cols = tuple(sorted(row.keys()))
            batches[cols].append((it, row))

        out_batches = []
        for cols, item_rows in batches.items():
            buf = io.StringIO()
            writer = csv.DictWriter(buf, fieldnames=list(cols), quoting=csv.QUOTE_ALL)
            writer.writeheader()

            for it, row in item_rows:
                # Verificación estricta de CERO celdas vacías
                assert all(row.get(c) for c in cols), f"Error de gobierno: Celda vacía detectada en lote para ítem {it.uuid_dspace}"
                writer.writerow(row)
                it.status = st_exportada
                db.add(DSpaceSyncLog(id_item_enrichment=it.id, sync_type="Export_CSV", http_status_code=200))

            db.commit()
            out_batches.append({
                "columns": list(cols),
                "total_rows": len(item_rows),
                "csv_content": buf.getvalue()
            })

        return out_batches

    # Alias para compatibilidad
    export_approved_proposals_csv = export_csv_zero_empty_cells

    # -------------------------------------------------------------------------
    # 6. ESTADOS FINALES: CARGADA Y CERRADA
    # -------------------------------------------------------------------------
    def mark_as_loaded(self, db: Session, item_id: uuid.UUID, http_status_code: int = 200) -> Dict[str, Any]:
        """
        Transita una propuesta desde 'Exportada' a 'Cargada' tras confirmarse
        la importación masiva o sincronización REST exitosa en DSpace-CRIS.
        """
        item = db.query(ItemEnrichment).filter(ItemEnrichment.id == item_id).first()
        if not item:
            return {"error": "Item no encontrado"}

        st_cargada = self.get_status_by_name(db, ProposalStatus.CARGADA)
        item.status = st_cargada
        db.add(DSpaceSyncLog(
            id_item_enrichment=item.id,
            sync_type="DSpace_Import_Verified",
            http_status_code=http_status_code
        ))
        db.commit()
        return {"result": "CARGADA", "item_id": str(item.id)}

    def mark_as_closed(self, db: Session, item_id: uuid.UUID) -> Dict[str, Any]:
        """
        Transita una propuesta desde 'Cargada' a 'Cerrada' completando
        el ciclo de vida formal de gobierno del dato.
        """
        item = db.query(ItemEnrichment).filter(ItemEnrichment.id == item_id).first()
        if not item:
            return {"error": "Item no encontrado"}

        st_cerrada = self.get_status_by_name(db, ProposalStatus.CERRADA)
        item.status = st_cerrada
        db.add(DSpaceSyncLog(
            id_item_enrichment=item.id,
            sync_type="Cycle_Closed",
            http_status_code=200
        ))
        db.commit()
        return {"result": "CERRADA", "item_id": str(item.id)}
