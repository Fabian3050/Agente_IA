"""
Procesamiento de DOIs y Publicaciones - Agente IA DSpace-CRIS V3.0
Ejecuta el pipeline completo según el Diagrama de Flujo V3 y la Especificación Técnica:
1. Monitoreo e Idempotencia temprana (MS4)
2. Recuperación y Validación en fuentes científicas con Fuzzy Matching (MS1)
3. Trazabilidad atómica por campo (Field_Proposal)
4. Clasificación jerárquica FORD OCDE y ODS ONU mediante LLM local Ollama (MS2)
5. Disponibilización en estado 'En_revision' para curaduría humana
"""

import asyncio
import sys
import os

# Asegurar que la ruta base esté en sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, Base, engine
from app.services.seed_service import run_full_seeding
from app.services.dspace_orchestrator_service import DSpaceOrchestratorServiceMS4
from app.models.db_models import ItemEnrichment, Status, ProposalStatus, DoiRecord


async def procesar_lote_v3():
    print("=================================================================")
    print("Iniciando Pipeline de Enriquecimiento y Clasificación V3.0")
    print("=================================================================")

    # 1. Asegurar tablas y catálogos iniciales
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    orchestrator = DSpaceOrchestratorServiceMS4()

    try:
        run_full_seeding(db)

        # 2. Obtener lista de publicaciones a procesar (desde ItemEnrichment o DoiRecord)
        items_a_procesar = db.query(ItemEnrichment).all()

        # Si no hay registros en ItemEnrichment, importar los de DoiRecord como transición
        if not items_a_procesar:
            dois_legacy = db.query(DoiRecord).all()
            if dois_legacy:
                print(f"[*] Migrando {len(dois_legacy)} DOIs desde DoiRecord al esquema V3...")
                for rec in dois_legacy:
                    orchestrator.handle_detected_item(
                        db=db,
                        uuid_dspace=f"legacy-uuid-{rec.id}",
                        doi=rec.doi,
                        title=f"Publicación DOI {rec.doi}"
                    )
                items_a_procesar = db.query(ItemEnrichment).all()

        # Si aún no hay, insertar lote por defecto de prueba
        if not items_a_procesar:
            print("[*] Insertando DOIs de prueba para el procesamiento...")
            test_dois = [
                ("item-uuid-001", "10.1177/16878140211010657", "Analysis of medical images using deep learning"),
                ("item-uuid-002", "10.1016/j.robot.2024.104661", "Adaptive robotics in manufacturing systems"),
                ("item-uuid-003", "10.1155/2020/7816785", "Machine Learning in Solar and Wind Renewable Energy"),
                ("item-uuid-004", "10.3390/ijms21217922", "Molecular Mechanisms of Plant Tolerance to Drought"),
                ("item-uuid-005", "10.5354/0719-2584.2025.74613", "Políticas públicas y educación superior en Chile")
            ]
            for uuid_dsp, doi_val, tit_val in test_dois:
                orchestrator.handle_detected_item(
                    db=db,
                    uuid_dspace=uuid_dsp,
                    doi=doi_val,
                    title=tit_val
                )
            items_a_procesar = db.query(ItemEnrichment).all()

        print(f"\n[+] Total de publicaciones en cola de procesamiento: {len(items_a_procesar)}\n")

        # 3. Iterar cada publicación en el flujo determinista V3
        for item in items_a_procesar:
            st_name = item.status.name if item.status else "Desconocido"
            print(f"-----------------------------------------------------------------")
            print(f"Ítem UUID DSpace: {item.uuid_dspace}")
            print(f"DOI: {item.doi} | Título: {item.title}")
            print(f"Estado Inicial: {st_name}")

            # 3.1 Idempotencia temprana: saltar si ya está en curaduría, exportado o cerrado
            if st_name in [ProposalStatus.EN_REVISION, ProposalStatus.APROBADA, ProposalStatus.EXPORTADA, ProposalStatus.CARGADA, ProposalStatus.CERRADA]:
                print(f"[SKIP] Omitido por Idempotencia Temprana (Estado: {st_name}).")
                continue

            # 3.2 Fase de Recuperación (MS1)
            print("[*] Ejecutando Fase 1: Recuperación en Fuentes Científicas (Crossref, OpenAlex, etc.)...")
            retrieval_res = await orchestrator.process_retrieval_for_item(db, item)
            print(f"  -> Resultado Recuperación: {retrieval_res.get('status')}")

            # Si derivó a coincidencia dudosa, se detiene para curaduría humana
            if item.status.name == ProposalStatus.EN_REVISION:
                print(f"  [!] Ítem derivado a '{item.status.name}' para revisión humana.")
                continue

            # 3.3 Fase de Clasificación LLM (MS2)
            if item.status.name == ProposalStatus.EN_CLASIFICACION:
                print("[*] Ejecutando Fase 2: Inferencia Semántica Local Ollama (OCDE & ODS)...")
                class_res = await orchestrator.process_classification_for_item(db, item)
                print(f"  -> Resultado Clasificación: {class_res.get('status')}")

            print(f"[✔] Proceso completado. Estado final del ítem: {item.status.name}")

    except Exception as e:
        print(f"[X] Error crítico en el proceso batch: {e}")
    finally:
        db.close()
        print("\n=================================================================")
        print("Pipeline V3 finalizado exitosamente.")
        print("=================================================================")

if __name__ == "__main__":
    asyncio.run(procesar_lote_v3())
