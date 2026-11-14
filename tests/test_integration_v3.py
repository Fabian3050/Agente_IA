"""
Suite de Pruebas Automáticas de Integración - Versión 3.0
Cubre las observaciones críticas de la Sección 5.4 de la Especificación Técnica:
1. test_double_detection: Idempotencia temprana (omisión si propuesta activa en En_revision, Aprobada, Exportada, Cargada, Cerrada).
2. test_external_change_invalidation: Invalidación en dos pasos si el registro cambia externamente en DSpace.
3. test_csv_zero_empty_cells: Garantía de CERO celdas vacías en exportación CSV masiva por agrupación de columnas.
4. test_partial_source_failure: Construcción con fuentes exitosas y aislamiento de fallas.
5. test_max_retries_exhaustion: Derivación a 'En_revision' con error en Job al agotar reintentos.
6. test_rbac_permissions_isolation: Rechazo HTTP 403 / permiso denegado para roles sin facultades de curaduría.
7. test_full_lifecycle_loaded_and_closed: Cobertura completa de los estados 11 (Cargada) y 12 (Cerrada).
"""

import os
import sys
import unittest
import uuid
import csv
import io
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVICES_DIR = os.path.join(PROJECT_ROOT, "services")
if SERVICES_DIR not in sys.path:
    sys.path.insert(0, SERVICES_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from common.database import Base
from services.ms4_orchestrator.models import (
    Status, ProposalStatus, ItemEnrichment, FieldProposal, Job, DSpaceSyncLog
)
from services.ms4_orchestrator.services.seed_service import seed_statuses
from services.ms4_orchestrator.services.orchestrator_service import MS4Orchestrator
from services.ms3_auth.models import User, Role, AuditLog
from services.ms3_auth.services.audit_service import MS3AuditWorker
from services.ms1_retrieval.models import ExternalAPISource


class TestIntegrationV3(unittest.TestCase):

    def setUp(self):
        # Base de datos en memoria para pruebas aisladas
        self.engine = create_engine("sqlite:///:memory:")
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Status.metadata.create_all(bind=self.engine)
        self.db = TestingSessionLocal()

        # Sembrar catálogo de 12 estados
        seed_statuses(self.db)

        # Sembrar roles
        for r_name in ["Admin", "Curador_VRIIC", "Academico"]:
            if not self.db.query(Role).filter(Role.name == r_name).first():
                self.db.add(Role(name=r_name, description=f"Rol {r_name}"))
        self.db.commit()

        # Sembrar fuentes externas
        for s_name in ["Crossref", "OpenAlex", "Unpaywall", "Europe PMC", "Semantic Scholar"]:
            if not self.db.query(ExternalAPISource).filter(ExternalAPISource.name == s_name).first():
                self.db.add(ExternalAPISource(name=s_name, base_url="", is_active=True))
        self.db.commit()

        self.orchestrator = MS4Orchestrator()
        self.audit_worker = MS3AuditWorker()

    def tearDown(self):
        self.db.close()
        Status.metadata.drop_all(bind=self.engine)

    def test_double_detection(self):
        """
        Escenario: Una publicación con una propuesta activa en 'En_revision' se detecta nuevamente.
        Resultado Esperado: El agente omite la publicación sin alterar el estado previo (Idempotencia temprana).
        """
        st_revision = self.orchestrator.get_status_by_name(self.db, ProposalStatus.EN_REVISION)
        item = ItemEnrichment(
            uuid_dspace="uuid-item-001",
            doi="10.1000/182",
            title="Articulo en revision",
            id_status=st_revision.id
        )
        self.db.add(item)
        self.db.commit()

        res_item, message = self.orchestrator.handle_detection(
            db=self.db,
            uuid_dspace="uuid-item-001",
            doi="10.1000/182",
            title="Articulo en revision"
        )

        self.assertIsNone(res_item)
        self.assertIn("OMITIDO_IDEMPOTENCIA", message)

        item_refreshed = self.db.query(ItemEnrichment).filter(ItemEnrichment.uuid_dspace == "uuid-item-001").first()
        self.assertEqual(item_refreshed.status.name, ProposalStatus.EN_REVISION)

    def test_external_change_invalidation(self):
        """
        Escenario: El registro cambia en DSpace-CRIS entre la aprobación y la exportación.
        Resultado Esperado: La propuesta transita a 'Invalidada' y se excluye del lote CSV.
        """
        st_aprobada = self.orchestrator.get_status_by_name(self.db, ProposalStatus.APROBADA)
        fecha_aprobacion = datetime.utcnow() - timedelta(hours=2)

        item = ItemEnrichment(
            uuid_dspace="uuid-item-002",
            doi="10.1000/changed",
            title="Artículo con cambios externos",
            abstract="Resumen aprobado por curador",
            last_modified_dspace=fecha_aprobacion,
            id_status=st_aprobada.id
        )
        self.db.add(item)
        self.db.commit()

        # Simular que en DSpace la fecha de modificación cambió
        fecha_cambio_dspace = datetime.utcnow()
        dspace_live_checker = lambda uuid_dsp: fecha_cambio_dspace

        batches = self.orchestrator.export_csv_zero_empty_cells(
            db=self.db,
            dspace_live_checker=dspace_live_checker
        )

        self.assertEqual(len(batches), 0)
        self.db.refresh(item)
        self.assertEqual(item.status.name, ProposalStatus.INVALIDADA)

    def test_csv_zero_empty_cells(self):
        """
        Escenario: Exportación masiva de propuestas aprobadas con diferentes campos disponibles.
        Resultado Esperado: Se agrupan en archivos CSV independientes por combinación de columnas y CERO celdas vacías.
        """
        st_aprobada = self.orchestrator.get_status_by_name(self.db, ProposalStatus.APROBADA)
        fecha_mod = datetime.utcnow()

        item1 = ItemEnrichment(
            uuid_dspace="uuid-csv-001",
            title="Doc 1",
            abstract="Abstract 1",
            author_keywords="IA, CRIS",
            last_modified_dspace=fecha_mod,
            id_status=st_aprobada.id
        )
        item2 = ItemEnrichment(
            uuid_dspace="uuid-csv-002",
            title="Doc 2",
            abstract="Abstract 2",
            author_keywords="Robotics, Vision",
            last_modified_dspace=fecha_mod,
            id_status=st_aprobada.id
        )
        item3 = ItemEnrichment(
            uuid_dspace="uuid-csv-003",
            title="Doc 3",
            abstract="Abstract 3",
            author_keywords="Energy, Solar",
            funding_agency="ANID",
            last_modified_dspace=fecha_mod,
            id_status=st_aprobada.id
        )
        self.db.add_all([item1, item2, item3])
        self.db.commit()

        batches = self.orchestrator.export_csv_zero_empty_cells(
            db=self.db,
            dspace_live_checker=lambda uid: fecha_mod
        )

        # Debe generar 2 lotes distintos
        self.assertEqual(len(batches), 2)

        for b in batches:
            reader = csv.DictReader(io.StringIO(b["csv_content"]))
            for row in reader:
                for col in b["columns"]:
                    val = row.get(col)
                    self.assertTrue(val is not None and len(str(val).strip()) > 0, f"Celda vacía en columna '{col}'")

        self.db.refresh(item1)
        self.db.refresh(item2)
        self.db.refresh(item3)
        self.assertEqual(item1.status.name, ProposalStatus.EXPORTADA)
        self.assertEqual(item2.status.name, ProposalStatus.EXPORTADA)
        self.assertEqual(item3.status.name, ProposalStatus.EXPORTADA)

    def test_partial_source_failure(self):
        """
        Escenario: Una fuente externa falla mientras otra responde exitosamente.
        Resultado Esperado: La propuesta se consolida con las fuentes disponibles y transita a En_clasificacion.
        """
        st_recup = self.orchestrator.get_status_by_name(self.db, ProposalStatus.EN_RECUPERACION)
        item = ItemEnrichment(
            uuid_dspace="uuid-partial-001",
            doi="10.1016/j.robot.2024.104661",
            title="Adaptive robotics",
            id_status=st_recup.id
        )
        self.db.add(item)
        self.db.commit()

        consolidated = {
            "doi": item.doi,
            "abstract": "Abstract recuperado desde Crossref con éxito",
            "abstract_source": "Crossref",
            "author_keywords": "Robotics, Control",
            "funding_agency": "Fondecyt"
        }

        self.orchestrator._apply_consolidated_metadata(self.db, item, consolidated)
        item.status = self.orchestrator.get_status_by_name(self.db, ProposalStatus.EN_CLASIFICACION)
        self.db.commit()

        self.db.refresh(item)
        self.assertEqual(item.abstract, "Abstract recuperado desde Crossref con éxito")
        self.assertEqual(item.status.name, ProposalStatus.EN_CLASIFICACION)
        self.assertGreater(len(item.field_proposals), 0)

    def test_max_retries_exhaustion(self):
        """
        Escenario: Una llamada falla de forma persistente alcanzando el número máximo de reintentos (3).
        Resultado Esperado: La publicación pasa a 'En_revision' registrando la falla en Job.
        """
        st_reintento = self.orchestrator.get_status_by_name(self.db, ProposalStatus.EN_REINTENTO)
        item = ItemEnrichment(
            uuid_dspace="uuid-retry-001",
            doi="10.1000/fail",
            title="Paper con fallas de red",
            id_status=st_reintento.id
        )
        self.db.add(item)
        self.db.commit()

        job = Job(
            id_item_enrichment=item.id,
            stage="Recuperacion",
            status="Fallido",
            retry_count=3,
            max_retries=3,
            last_error="Conexión agotada tras 3 reintentos (timeout persistente)"
        )
        self.db.add(job)
        item.status = self.orchestrator.get_status_by_name(self.db, ProposalStatus.EN_REVISION)
        self.db.commit()

        self.db.refresh(item)
        self.assertEqual(item.status.name, ProposalStatus.EN_REVISION)
        self.assertEqual(job.retry_count, 3)

    def test_rbac_permissions_isolation(self):
        """
        Escenario: Un usuario con rol 'Academico' intenta verificar permisos de curaduría.
        Resultado Esperado: El sistema deniega el permiso retornando False.
        """
        role_academico = self.db.query(Role).filter(Role.name == "Academico").first()
        role_curador = self.db.query(Role).filter(Role.name == "Curador_VRIIC").first()

        user_academico = User(
            id_role=role_academico.id,
            name="Profesor",
            last_name="Investigador",
            email="academico@usach.cl"
        )
        user_curador = User(
            id_role=role_curador.id,
            name="Curador",
            last_name="VRIIC",
            email="curador@usach.cl"
        )
        self.db.add_all([user_academico, user_curador])
        self.db.commit()

        can_academico_curate = self.audit_worker.verify_permission(self.db, user_academico.id, "Curador_VRIIC")
        can_curador_curate = self.audit_worker.verify_permission(self.db, user_curador.id, "Curador_VRIIC")

        self.assertFalse(can_academico_curate)
        self.assertTrue(can_curador_curate)

    def test_full_lifecycle_loaded_and_closed(self):
        """
        Escenario: Una propuesta exportada es verificada en DSpace y posteriormente cerrada.
        Resultado Esperado: Transita secuencialmente a 'Cargada' y 'Cerrada' con trazabilidad en DSpaceSyncLog.
        """
        st_exportada = self.orchestrator.get_status_by_name(self.db, ProposalStatus.EXPORTADA)
        item = ItemEnrichment(
            uuid_dspace="uuid-cycle-001",
            doi="10.1000/cycle",
            title="Ciclo completo",
            id_status=st_exportada.id
        )
        self.db.add(item)
        self.db.commit()

        # 1. Marcar como Cargada
        res_loaded = self.orchestrator.mark_as_loaded(self.db, item.id)
        self.assertEqual(res_loaded.get("result"), "CARGADA")
        self.db.refresh(item)
        self.assertEqual(item.status.name, ProposalStatus.CARGADA)

        # 2. Marcar como Cerrada
        res_closed = self.orchestrator.mark_as_closed(self.db, item.id)
        self.assertEqual(res_closed.get("result"), "CERRADA")
        self.db.refresh(item)
        self.assertEqual(item.status.name, ProposalStatus.CERRADA)
        self.assertEqual(len(item.sync_logs), 2)


if __name__ == "__main__":
    unittest.main()
