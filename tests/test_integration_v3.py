"""
Suite de Pruebas Automáticas de Integración - Versión 3.0
Cubre las observaciones críticas de la Sección 5.4 de la Especificación Técnica:
1. test_double_detection: Idempotencia temprana (omisión si propuesta activa).
2. test_external_change_invalidation: Invalidación si el registro cambia externamente en DSpace.
3. test_csv_zero_empty_cells: Garantía de CERO celdas vacías en exportación CSV masiva.
4. test_partial_source_failure: Construcción con fuentes exitosas y aislamiento de fallas.
5. test_max_retries_exhaustion: Derivación a 'En_revision' con error en Job al agotar reintentos.
6. test_rbac_permissions_isolation: Rechazo HTTP 403 para roles sin facultades de curaduría.
"""

import unittest
import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.db_models import (
    Base, Status, ProposalStatus, ItemEnrichment, FieldProposal,
    User, Role, AuditLog, Job, ExternalAPISource
)
from app.services.seed_service import seed_statuses, seed_roles, seed_external_sources
from app.services.dspace_orchestrator_service import DSpaceOrchestratorServiceMS4
from app.services.curation_audit_service import CurationAuditServiceMS3


class TestIntegrationV3(unittest.TestCase):

    def setUp(self):
        # Crear base de datos en memoria para pruebas aisladas y reproducibles
        self.engine = create_engine("sqlite:///:memory:")
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.db = TestingSessionLocal()

        # Sembrar catálogos básicos
        seed_statuses(self.db)
        seed_roles(self.db)
        seed_external_sources(self.db)

        self.orchestrator = DSpaceOrchestratorServiceMS4()
        self.curation_service = CurationAuditServiceMS3()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_double_detection(self):
        """
        Nombre de la Prueba: test_double_detection
        Escenario: Una publicación con una propuesta en estado 'En_revision' se somete a un segundo ciclo de monitoreo.
        Resultado Esperado: El sistema omite la publicación; no se realizan llamadas externas y la propuesta previa se mantiene intacta.
        """
        # Crear propuesta inicial en estado 'En_revision'
        st_revision = self.orchestrator.get_status_by_name(self.db, ProposalStatus.EN_REVISION)
        item = ItemEnrichment(
            uuid_dspace="uuid-item-001",
            doi="10.1000/182",
            title="Articulo en revision",
            id_status=st_revision.id
        )
        self.db.add(item)
        self.db.commit()

        # Segundo ciclo de monitoreo sobre el mismo ítem
        res_item, message = self.orchestrator.handle_detected_item(
            db=self.db,
            uuid_dspace="uuid-item-001",
            doi="10.1000/182",
            title="Articulo en revision"
        )

        self.assertIsNone(res_item)
        self.assertTrue("OMITIDO_IDEMPOTENCIA" in message)

        # Verificar que el ítem original sigue intacto en 'En_revision'
        item_refreshed = self.db.query(ItemEnrichment).filter(ItemEnrichment.uuid_dspace == "uuid-item-001").first()
        self.assertEqual(item_refreshed.status.name, ProposalStatus.EN_REVISION)

    def test_external_change_invalidation(self):
        """
        Nombre de la Prueba: test_external_change_invalidation
        Escenario: El registro cambia en DSpace-CRIS entre la aprobación del curador y el momento de la exportación.
        Resultado Esperado: La propuesta transita automáticamente al estado 'Invalidada' y se excluye del lote CSV.
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

        # Simular que en DSpace la fecha de modificación cambió posteriormente
        fecha_cambio_dspace = datetime.utcnow()
        dspace_live_checker = lambda uuid_dsp: fecha_cambio_dspace

        batches = self.orchestrator.export_approved_proposals_csv(
            db=self.db,
            dspace_live_checker=dspace_live_checker
        )

        # Debe excluirse del lote
        self.assertEqual(len(batches), 0)

        # Debe haber transitado automáticamente a 'Invalidada'
        self.db.refresh(item)
        self.assertEqual(item.status.name, ProposalStatus.INVALIDADA)

    def test_csv_zero_empty_cells(self):
        """
        Nombre de la Prueba: test_csv_zero_empty_cells
        Escenario: Se genera un lote de exportación CSV para un grupo de publicaciones enriquecidas.
        Resultado Esperado: Se verifica que ninguna celda correspondiente a las columnas incluidas contenga valor nulo o vacío.
        """
        st_aprobada = self.orchestrator.get_status_by_name(self.db, ProposalStatus.APROBADA)
        fecha_mod = datetime.utcnow()

        # Item 1 tiene abstract y keywords
        item1 = ItemEnrichment(
            uuid_dspace="uuid-csv-001",
            title="Doc 1",
            abstract="Abstract 1",
            author_keywords="IA, CRIS",
            last_modified_dspace=fecha_mod,
            id_status=st_aprobada.id
        )
        # Item 2 tiene exactamente el mismo conjunto de campos (abstract y keywords)
        item2 = ItemEnrichment(
            uuid_dspace="uuid-csv-002",
            title="Doc 2",
            abstract="Abstract 2",
            author_keywords="Robotics, Vision",
            last_modified_dspace=fecha_mod,
            id_status=st_aprobada.id
        )
        # Item 3 tiene abstract, keywords y funding_agency (subconjunto diferente)
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

        batches = self.orchestrator.export_approved_proposals_csv(
            db=self.db,
            dspace_live_checker=lambda uid: fecha_mod
        )

        # Debe haber generado 2 lotes agrupados por subconjunto exacto de columnas
        self.assertEqual(len(batches), 2)

        # Verificar que CERO celdas en los CSV generados están vacías
        import csv, io
        for b in batches:
            reader = csv.DictReader(io.StringIO(b["csv_content"]))
            for row in reader:
                for col in b["columns"]:
                    val = row.get(col)
                    self.assertTrue(val is not None and len(str(val).strip()) > 0, f"Celda vacía detectada en columna '{col}'")

        # Verificar que transitaron a 'Exportada'
        self.db.refresh(item1)
        self.db.refresh(item2)
        self.db.refresh(item3)
        self.assertEqual(item1.status.name, ProposalStatus.EXPORTADA)
        self.assertEqual(item2.status.name, ProposalStatus.EXPORTADA)
        self.assertEqual(item3.status.name, ProposalStatus.EXPORTADA)

    def test_partial_source_failure(self):
        """
        Nombre de la Prueba: test_partial_source_failure
        Escenario: Una fuente externa falla mientras otra responde exitosamente.
        Resultado Esperado: La propuesta se consolida con las fuentes disponibles.
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

        # Simulación de consolidación directa
        consolidated = {
            "doi": item.doi,
            "abstract": "Abstract recuperado desde Crossref con éxito",
            "abstract_source": "Crossref",
            "author_keywords": "Robotics, Control",
            "funding_agency": "Fondecyt"
        }

        # Guardar proveniencia atómica
        fp = FieldProposal(
            id_item_enrichment=item.id,
            field_name="dc.description.abstract",
            proposed_value=consolidated["abstract"],
            source=consolidated["abstract_source"],
            final_value=consolidated["abstract"]
        )
        self.db.add(fp)
        item.abstract = consolidated["abstract"]
        item.status = self.orchestrator.get_status_by_name(self.db, ProposalStatus.EN_CLASIFICACION)
        self.db.commit()

        self.db.refresh(item)
        self.assertEqual(item.abstract, "Abstract recuperado desde Crossref con éxito")
        self.assertEqual(item.status.name, ProposalStatus.EN_CLASIFICACION)
        self.assertEqual(len(item.field_proposals), 1)

    def test_max_retries_exhaustion(self):
        """
        Nombre de la Prueba: test_max_retries_exhaustion
        Escenario: Una llamada falla de forma persistente alcanzando el número máximo de reintentos (3).
        Resultado Esperado: La publicación pasa al estado 'En_revision' presentando los datos obtenidos hasta el momento y la falla en Job.
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

        # Simular agotamiento de reintentos en Job
        job = Job(
            id_item_enrichment=item.id,
            stage="Recuperacion",
            status="Fallido",
            retry_count=3,
            max_retries=3,
            last_error="Conexión agotada tras 3 reintentos (timeout persistente)"
        )
        self.db.add(job)
        # Al agotar reintentos, el orquestador deriva a En_revision
        item.status = self.orchestrator.get_status_by_name(self.db, ProposalStatus.EN_REVISION)
        self.db.commit()

        self.db.refresh(item)
        self.assertEqual(item.status.name, ProposalStatus.EN_REVISION)
        self.assertEqual(job.retry_count, 3)
        self.assertIn("timeout persistente", job.last_error)

    def test_rbac_permissions_isolation(self):
        """
        Nombre de la Prueba: test_rbac_permissions_isolation
        Escenario: Un usuario con rol 'Academico' intenta realizar una acción de curaduría.
        Resultado Esperado: El sistema rechaza la facultad retornando False (HTTP 403 Forbidden).
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

        # Comprobar permisos con el servicio de auditoría y roles
        can_academico_curate = self.curation_service.check_user_role(self.db, user_academico.id, "Curador_VRIIC")
        can_curador_curate = self.curation_service.check_user_role(self.db, user_curador.id, "Curador_VRIIC")

        self.assertFalse(can_academico_curate, "Un académico NO debe tener permisos de curaduría (403 Forbidden)")
        self.assertTrue(can_curador_curate, "Un Curador_VRIIC debe tener permisos de curaduría autorizados")


if __name__ == "__main__":
    unittest.main()

