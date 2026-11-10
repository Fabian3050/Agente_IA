import csv
import io
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Callable
from collections import defaultdict
from sqlalchemy.orm import Session

from app.models.db_models import (
    ItemEnrichment, Status, ProposalStatus,
    FieldProposal, ItemCategory, Category,
    Job, DSpaceSyncLog, AuditLog
)
from app.services.retrieval_service import MetadataRetrievalServiceMS1
from app.services.classification_service import ClassificationService
from app.services.curation_audit_service import CurationAuditServiceMS3


class DSpaceOrchestratorServiceMS4:
    """
    Microservicio 4: Conexión, Orquestación e Integración DSpace-CRIS (MS4).
    Gestiona el ciclo de vida estricto (12 estados), proveniencia atómica (FieldProposal),
    concurrencia, idempotencia temprana y exportación segura por CSV (cero celdas vacías).
    Escribe exclusivamente en Item_Enrichment, Field_Proposal, Item_Category, Status, Job y DSpace_Sync_Log.
    """

    def __init__(self):
        self.retrieval_service = MetadataRetrievalServiceMS1()
        self.classification_service = ClassificationService()
        self.audit_service = CurationAuditServiceMS3()

    def get_status_by_name(self, db: Session, name: str) -> Status:
        st = db.query(Status).filter(Status.name == name).first()
        if not st:
            st = Status(name=name, description=f"Estado {name}")
            db.add(st)
            db.commit()
            db.refresh(st)
        return st

    # -------------------------------------------------------------------------
    # 1. MONITOREO E IDEMPOTENCIA TEMPRANA (Sección 1.3 / Bloque 1)
    # -------------------------------------------------------------------------
    def handle_detected_item(
        self,
        db: Session,
        uuid_dspace: str,
        doi: Optional[str] = None,
        title: Optional[str] = None,
        last_modified_dspace: Optional[datetime] = None,
        force_reprocess: bool = False
    ) -> Tuple[Optional[ItemEnrichment], str]:
        """
        Evalúa un ítem detectado con campos faltantes en DSpace-CRIS.
        Implementa Idempotencia Temprana:
        - Si está en En_revision, Aprobada, Exportada, Cargada, Cerrada o en proceso -> OMITIR.
        - Si está Invalidada -> si cambió en DSpace, pasa a Detectada para re-evaluar.
        - Si está Rechazada -> solo si el curador lo habilita (force_reprocess=True).
        - Si no existe -> crea ItemEnrichment en Detectada y transita a En_recuperacion.
        """
        existing = db.query(ItemEnrichment).filter(ItemEnrichment.uuid_dspace == uuid_dspace).first()

        if existing:
            status_name = existing.status.name if existing.status else ""

            # Idempotencia: omitir estados activos de curaduría, exportados o cerrados
            omitted_statuses = [
                ProposalStatus.EN_REVISION,
                ProposalStatus.APROBADA,
                ProposalStatus.EXPORTADA,
                ProposalStatus.CARGADA,
                ProposalStatus.CERRADA,
                ProposalStatus.EN_RECUPERACION,
                ProposalStatus.EN_CLASIFICACION,
                ProposalStatus.EN_REINTENTO
            ]
            if status_name in omitted_statuses:
                return None, f"OMITIDO_IDEMPOTENCIA: El ítem {uuid_dspace} ya se encuentra en estado '{status_name}'"

            # Si estaba invalidada y cambió en DSpace -> reabrir a Detectada
            if status_name == ProposalStatus.INVALIDADA:
                if last_modified_dspace and existing.last_modified_dspace != last_modified_dspace:
                    existing.last_modified_dspace = last_modified_dspace
                    existing.status = self.get_status_by_name(db, ProposalStatus.DETECTADA)
                    db.commit()
                    return existing, "REABIERTA_POR_CAMBIO_DSPACE"
                else:
                    return None, "OMITIDO: Registro invalidado sin cambios externos"

            # Si estaba rechazada -> solo reprocesar si el curador lo habilitó
            if status_name == ProposalStatus.RECHAZADA:
                if force_reprocess:
                    existing.status = self.get_status_by_name(db, ProposalStatus.DETECTADA)
                    db.commit()
                    return existing, "REPROCESO_HABILITADO_POR_CURADOR"
                else:
                    return None, "OMITIDO: Registro rechazado por curador"

        # Si no existe -> crear registro base en 'Detectada'
        st_detectada = self.get_status_by_name(db, ProposalStatus.DETECTADA)
        new_item = ItemEnrichment(
            uuid_dspace=uuid_dspace,
            doi=doi,
            title=title,
            last_modified_dspace=last_modified_dspace,
            id_status=st_detectada.id
        )
        db.add(new_item)
        db.commit()
        db.refresh(new_item)

        # Transitar inmediatamente a 'En_recuperacion'
        new_item.status = self.get_status_by_name(db, ProposalStatus.EN_RECUPERACION)
        db.commit()
        return new_item, "CREADA_Y_EN_RECUPERACION"

    # -------------------------------------------------------------------------
    # 2. RECUPERACIÓN Y VALIDACIÓN (MS1 / Bloque 2)
    # -------------------------------------------------------------------------
    async def process_retrieval_for_item(self, db: Session, item: ItemEnrichment) -> Dict[str, Any]:
        """
        Ejecuta la fase de recuperación (MS1) y almacena la proveniencia atómica (FieldProposal).
        Transita según el resultado a En_clasificacion, Coincidencia_dudosa o En_reintento.
        """
        # Registrar Job de Recuperación
        job = Job(
            id_item_enrichment=item.id,
            stage="Recuperacion",
            status="En_Progreso",
            created_at=datetime.utcnow()
        )
        db.add(job)
        db.commit()

        try:
            retrieval_data = await self.retrieval_service.retrieve_for_item(item, db)
            outcome = retrieval_data["outcome"]
            consolidated = retrieval_data["consolidated"]

            # Si la coincidencia es dudosa -> transitar a Coincidencia_dudosa -> En_revision
            if outcome == "COINCIDENCIA_DUDOSA":
                item.status = self.get_status_by_name(db, ProposalStatus.COINCIDENCIA_DUDOSA)
                job.status = "Completado"
                job.last_error = "Coincidencia dudosa: similitud textual inferior al umbral seguro"
                db.commit()

                # Transitar a En_revision para revisión humana obligada
                item.status = self.get_status_by_name(db, ProposalStatus.EN_REVISION)
                db.commit()
                return {"stage": "recuperacion", "status": "COINCIDENCIA_DUDOSA", "item_id": str(item.id)}

            # Si se descartó por falta de datos o similitud insuficiente
            if outcome == "DESCARTADA" or outcome == "SIN_DATOS":
                job.status = "Fallido"
                job.last_error = f"Sin candidatos viables: {outcome}"
                item.status = self.get_status_by_name(db, ProposalStatus.EN_REVISION)
                db.commit()
                return {"stage": "recuperacion", "status": outcome, "item_id": str(item.id)}

            # Coincidencia alta: Consolidar campos en ItemEnrichment y FieldProposal
            if consolidated.get("doi"):
                item.doi = consolidated["doi"]
            if consolidated.get("abstract"):
                item.abstract = consolidated["abstract"]
            if consolidated.get("author_keywords"):
                item.author_keywords = consolidated["author_keywords"]
            if consolidated.get("automated_concepts"):
                item.automated_concepts = consolidated["automated_concepts"]
            if consolidated.get("funding_agency"):
                item.funding_agency = consolidated["funding_agency"]
            if consolidated.get("funding_id"):
                item.funding_id = consolidated["funding_id"]
            if consolidated.get("funding_grant_number"):
                item.funding_grant_number = consolidated["funding_grant_number"]
            if consolidated.get("oa_status"):
                item.oa_status = consolidated["oa_status"]
            if consolidated.get("license"):
                item.license = consolidated["license"]
            if consolidated.get("version_type"):
                item.version_type = consolidated["version_type"]

            # Guardar proveniencia atómica en FieldProposal (Sección 3.3)
            fields_map = [
                ("dc.description.abstract", consolidated.get("abstract"), consolidated.get("abstract_source"), "prioridad_confiabilidad_crossref_openalex"),
                ("dc.subject", consolidated.get("author_keywords"), "Fuentes combinadas", "palabras_clave_autor_explicitas"),
                ("cris.concept", consolidated.get("automated_concepts"), "OpenAlex", "conceptos_algoritmicos_controlados"),
                ("funding_agency", consolidated.get("funding_agency"), "Crossref/OpenAlex", "desglose_financiamiento"),
                ("oa_status", consolidated.get("oa_status"), "Unpaywall/OpenAlex", "clasificacion_estandar_open_access"),
                ("license", consolidated.get("license"), "Unpaywall/Crossref", "licencia_reutilizacion"),
                ("version_type", consolidated.get("version_type"), "Unpaywall/OpenAlex", "version_manuscrito")
            ]

            for field_name, prop_val, src, rule in fields_map:
                if prop_val:
                    fp = FieldProposal(
                        id_item_enrichment=item.id,
                        field_name=field_name,
                        original_dspace_value=None,
                        proposed_value=str(prop_val),
                        source=src,
                        rule_applied=rule,
                        final_value=str(prop_val),
                        is_edited_by_curator=False
                    )
                    db.add(fp)

            job.status = "Completado"
            # Transitar a En_clasificacion
            item.status = self.get_status_by_name(db, ProposalStatus.EN_CLASIFICACION)
            db.commit()

            return {"stage": "recuperacion", "status": "ALTA_COINCIDENCIA", "item_id": str(item.id)}

        except Exception as e:
            job.status = "Fallido"
            job.retry_count += 1
            job.last_error = str(e)
            if job.retry_count < job.max_retries:
                item.status = self.get_status_by_name(db, ProposalStatus.EN_REINTENTO)
            else:
                item.status = self.get_status_by_name(db, ProposalStatus.EN_REVISION)
            db.commit()
            return {"stage": "recuperacion", "status": "ERROR", "error": str(e), "item_id": str(item.id)}

    # -------------------------------------------------------------------------
    # 3. CLASIFICACIÓN OCDE / ODS (MS2 / Bloque 3)
    # -------------------------------------------------------------------------
    async def process_classification_for_item(self, db: Session, item: ItemEnrichment) -> Dict[str, Any]:
        """
        Ejecuta la inferencia LLM (MS2) y asocia las categorías en ItemCategory (MS4).
        Transita a En_revision.
        """
        job = Job(
            id_item_enrichment=item.id,
            stage="Clasificacion",
            status="En_Progreso",
            created_at=datetime.utcnow()
        )
        db.add(job)
        db.commit()

        try:
            res = await self.classification_service.classify_item_for_enrichment(
                item_id=item.id,
                title=item.title,
                abstract=item.abstract,
                keywords=item.author_keywords,
                db=db
            )

            # Asignar categorías OCDE en ItemCategory
            ocde_resp = res.get("ocde")
            if ocde_resp and ocde_resp.clasificaciones:
                for idx, c in enumerate(ocde_resp.clasificaciones[:2], start=1):
                    # Buscar o registrar Category
                    cat = db.query(Category).filter(
                        Category.scheme == "OCDE",
                        Category.code == c.codigo_disciplina
                    ).first()
                    if not cat:
                        cat = Category(
                            code=c.codigo_disciplina,
                            name=c.nombre_disciplina,
                            scheme="OCDE",
                            version="2007",
                            description=f"Área: {c.nombre_area}"
                        )
                        db.add(cat)
                        db.commit()
                        db.refresh(cat)

                    ic = ItemCategory(
                        id_item_enrichment=item.id,
                        id_category=cat.id,
                        origin="LLM",
                        priority_order=idx,
                        confidence_score=c.confidence_score
                    )
                    db.add(ic)

            # Asignar categorías ODS en ItemCategory
            ods_resp = res.get("ods")
            if ods_resp and ods_resp.clasificaciones:
                for idx, c in enumerate(ods_resp.clasificaciones[:2], start=1):
                    cat_ods_code = f"ODS {c.numero_ods}" if not c.numero_ods.startswith("ODS") else c.numero_ods
                    cat = db.query(Category).filter(
                        Category.scheme == "ODS",
                        Category.code == cat_ods_code
                    ).first()
                    if not cat:
                        cat = Category(
                            code=cat_ods_code,
                            name=c.nombre_ods,
                            scheme="ODS",
                            version="2015",
                            description=c.justificacion
                        )
                        db.add(cat)
                        db.commit()
                        db.refresh(cat)

                    ic = ItemCategory(
                        id_item_enrichment=item.id,
                        id_category=cat.id,
                        origin="LLM",
                        priority_order=idx,
                        confidence_score=c.confidence_score
                    )
                    db.add(ic)

            job.status = "Completado"
            # Transitar a En_revision (disponible para el curador humano)
            item.status = self.get_status_by_name(db, ProposalStatus.EN_REVISION)
            db.commit()
            return {"stage": "clasificacion", "status": "COMPLETADA", "item_id": str(item.id)}

        except Exception as e:
            job.status = "Fallido"
            job.retry_count += 1
            job.last_error = str(e)
            if job.retry_count < job.max_retries:
                item.status = self.get_status_by_name(db, ProposalStatus.EN_REINTENTO)
            else:
                item.status = self.get_status_by_name(db, ProposalStatus.EN_REVISION)
            db.commit()
            return {"stage": "clasificacion", "status": "ERROR", "error": str(e), "item_id": str(item.id)}

    # -------------------------------------------------------------------------
    # 4. CURADURÍA HUMANA Y REVALIDACIÓN DE CONCURRENCIA (MS3 / MS4 / Bloque 4)
    # -------------------------------------------------------------------------
    def apply_curator_decision(
        self,
        db: Session,
        item: ItemEnrichment,
        user_id: Any,
        decision: str,  # 'Aprobar', 'Rechazar', 'Editar'
        edited_fields: Optional[Dict[str, str]] = None,
        rejection_reason: Optional[str] = None,
        dspace_live_last_modified: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Aplica la decisión del curador verificando concurrencia:
        - Si el registro cambió en DSpace -> transita a Invalidada.
        - Si no cambió:
          - Rechazar -> transita a Rechazada + AuditLog inmutable.
          - Aprobar/Editar -> consolida FieldProposal, actualiza ItemEnrichment,
            registra en AuditLog y transita a Aprobada.
        """
        # Revalidación de concurrencia: ¿Cambió en DSpace antes o durante la curaduría?
        if dspace_live_last_modified and item.last_modified_dspace:
            if dspace_live_last_modified != item.last_modified_dspace:
                item.status = self.get_status_by_name(db, ProposalStatus.INVALIDADA)
                self.audit_service.record_curation_action(
                    db=db,
                    user_id=user_id,
                    item_id=item.id,
                    action="Invalidar",
                    rejection_reason="Registro modificado externamente en DSpace-CRIS durante curaduría."
                )
                db.commit()
                return {"result": "INVALIDADA", "message": "El registro fue modificado en DSpace antes de finalizar curaduría."}

        previous_data = {
            "title": item.title,
            "abstract": item.abstract,
            "author_keywords": item.author_keywords,
            "funding_agency": item.funding_agency,
            "oa_status": item.oa_status
        }

        if decision == "Rechazar":
            item.status = self.get_status_by_name(db, ProposalStatus.RECHAZADA)
            self.audit_service.record_curation_action(
                db=db,
                user_id=user_id,
                item_id=item.id,
                action="Rechazar",
                previous_value=previous_data,
                rejection_reason=rejection_reason or "Desestimada por curador"
            )
            db.commit()
            return {"result": "RECHAZADA", "message": "Propuesta rechazada y auditada exitosamente."}

        # Aprobar o Editar
        if edited_fields:
            for field_name, new_val in edited_fields.items():
                # Actualizar FieldProposal atómico
                fp = db.query(FieldProposal).filter(
                    FieldProposal.id_item_enrichment == item.id,
                    FieldProposal.field_name == field_name
                ).first()
                if fp:
                    fp.final_value = new_val
                    fp.is_edited_by_curator = True
                else:
                    db.add(FieldProposal(
                        id_item_enrichment=item.id,
                        field_name=field_name,
                        proposed_value=new_val,
                        final_value=new_val,
                        is_edited_by_curator=True
                    ))

                # Actualizar campo en ItemEnrichment
                if field_name == "dc.description.abstract": item.abstract = new_val
                elif field_name == "dc.subject": item.author_keywords = new_val
                elif field_name == "funding_agency": item.funding_agency = new_val
                elif field_name == "oa_status": item.oa_status = new_val

        item.status = self.get_status_by_name(db, ProposalStatus.APROBADA)
        new_data = {
            "title": item.title,
            "abstract": item.abstract,
            "author_keywords": item.author_keywords,
            "funding_agency": item.funding_agency,
            "oa_status": item.oa_status
        }
        self.audit_service.record_curation_action(
            db=db,
            user_id=user_id,
            item_id=item.id,
            action="Editar" if edited_fields else "Aprobar",
            previous_value=previous_data,
            new_value=new_data
        )
        db.commit()
        return {"result": "APROBADA", "message": "Propuesta aprobada y lista para lote de exportación."}

    # -------------------------------------------------------------------------
    # 5. PROTOCOLO DE EXPORTACIÓN SEGURA POR CSV - CERO CELDAS VACÍAS (Sección 1.4)
    # -------------------------------------------------------------------------
    def export_approved_proposals_csv(
        self,
        db: Session,
        dspace_live_checker: Optional[Callable[[str], Optional[datetime]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Ejecuta el protocolo estricto de exportación CSV según Sección 1.4:
        1. Revalidación previa de modificación: si cambió en DSpace -> pasa a Invalidada y se excluye.
        2. Agrupación por subconjunto de columnas: genera lotes CSV independientes para cada
           combinación exacta de columnas, garantizando CERO celdas vacías.
        3. Transita las propuestas exportadas al estado 'Exportada' y registra DSpaceSyncLog.
        """
        st_aprobada = self.get_status_by_name(db, ProposalStatus.APROBADA)
        st_exportada = self.get_status_by_name(db, ProposalStatus.EXPORTADA)
        st_invalidada = self.get_status_by_name(db, ProposalStatus.INVALIDADA)

        items_aprobados = db.query(ItemEnrichment).filter(ItemEnrichment.id_status == st_aprobada.id).all()
        if not items_aprobados:
            return []

        valid_items_to_export = []

        # 1. Revalidación de modificación
        for item in items_aprobados:
            if dspace_live_checker:
                live_modified = dspace_live_checker(item.uuid_dspace)
                if live_modified and item.last_modified_dspace and live_modified != item.last_modified_dspace:
                    # Cambió en DSpace -> transita a Invalidada
                    item.status = st_invalidada
                    db.commit()
                    continue
            valid_items_to_export.append(item)

        # 2. Agrupación por conjunto idéntico de columnas para CERO celdas vacías
        # Mapeo de campos a columnas de CSV DSpace
        batches_by_columns = defaultdict(list)

        for item in valid_items_to_export:
            row_dict = {"id": item.uuid_dspace}
            if item.abstract and item.abstract.strip():
                row_dict["dc.description.abstract"] = item.abstract.strip()
            if item.author_keywords and item.author_keywords.strip():
                row_dict["dc.subject"] = item.author_keywords.strip()
            if item.automated_concepts and item.automated_concepts.strip():
                row_dict["cris.concept"] = item.automated_concepts.strip()
            if item.funding_agency and item.funding_agency.strip():
                row_dict["dc.description.sponsorship"] = item.funding_agency.strip()
            if item.funding_grant_number and item.funding_grant_number.strip():
                row_dict["dc.relation.grantno"] = item.funding_grant_number.strip()
            if item.oa_status and item.oa_status.strip():
                row_dict["dc.rights.accessRights"] = item.oa_status.strip()

            # Llave única: tuple ordenada de nombres de columnas presentes
            col_keys = tuple(sorted(row_dict.keys()))
            batches_by_columns[col_keys].append((item, row_dict))

        generated_csv_batches = []

        # 3. Generar CSVs independientes por combinación
        for col_keys, items_and_rows in batches_by_columns.items():
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=list(col_keys), quoting=csv.QUOTE_ALL)
            writer.writeheader()

            for item, row in items_and_rows:
                # Verificación estricta de CERO celdas vacías
                assert all(row.get(col) for col in col_keys), "Violación de protocolo: celda vacía detectada!"
                writer.writerow(row)

                # Transitar propuesta a 'Exportada'
                item.status = st_exportada

                # Registrar log de sincronización
                sync_log = DSpaceSyncLog(
                    id_item_enrichment=item.id,
                    http_status_code=200,
                    sync_type="Export_CSV",
                    synced_at=datetime.utcnow()
                )
                db.add(sync_log)

            db.commit()

            generated_csv_batches.append({
                "columns": list(col_keys),
                "total_rows": len(items_and_rows),
                "csv_content": output.getvalue()
            })

        return generated_csv_batches

    # -------------------------------------------------------------------------
    # 6. CONFIRMACIÓN DE CARGA Y CIERRE (Sección 1.4 / Bloque 6)
    # -------------------------------------------------------------------------
    def confirm_ingestion_and_close(
        self,
        db: Session,
        item: ItemEnrichment,
        dspace_live_metadata_checker: Callable[[str], Dict[str, Any]]
    ) -> str:
        """
        En el siguiente ciclo de monitoreo, verifica si los metadatos aprobados
        fueron efectivamente ingestados en DSpace-CRIS:
        - Si confirmados -> transita a Cargada y finalmente a Cerrada.
        - Si aún no -> permanece en Exportada.
        """
        if item.status.name != ProposalStatus.EXPORTADA:
            return f"Estado no elegible: {item.status.name}"

        live_data = dspace_live_metadata_checker(item.uuid_dspace)

        # Verificar que al menos los campos enriquecidos estén presentes
        all_confirmed = True
        if item.abstract and not live_data.get("abstract"):
            all_confirmed = False
        if item.author_keywords and not live_data.get("keywords"):
            all_confirmed = False

        if all_confirmed:
            st_cargada = self.get_status_by_name(db, ProposalStatus.CARGADA)
            st_cerrada = self.get_status_by_name(db, ProposalStatus.CERRADA)
            
            item.status = st_cargada
            db.commit()

            # Transición inmediata al estado final de cierre
            item.status = st_cerrada
            
            sync_log = DSpaceSyncLog(
                id_item_enrichment=item.id,
                http_status_code=200,
                sync_type="Verification",
                synced_at=datetime.utcnow()
            )
            db.add(sync_log)
            db.commit()
            return "CONFIRMADO_Y_CERRADO"
        else:
            return "PERMANECE_EN_EXPORTADA"

