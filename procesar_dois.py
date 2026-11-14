"""
Procesamiento de DOIs y Publicaciones - Agente IA DSpace-CRIS V3.0
CLI Runner desacoplado para la Arquitectura de Microservicios (services/ms*/):
1. Monitoreo e Idempotencia temprana (MS4)
2. Recuperación y Validación en fuentes científicas con Fuzzy Matching (MS1 vía REST/RabbitMQ)
3. Trazabilidad atómica por campo (Field_Proposal)
4. Clasificación jerárquica FORD OCDE y ODS ONU mediante LLM local Ollama (MS2)
5. Disponibilización en estado 'En_revision' para curaduría humana en MS4
"""

import asyncio
import sys
import os
import uuid

# Configurar path raíz del proyecto
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Importar desde la arquitectura de microservicios desacoplada (services/)
from services.common.database import SessionLocal, Base, engine
from services.ms4_orchestrator.services.seed_service import run_full_seeding
from services.ms4_orchestrator.services.orchestrator_service import MS4Orchestrator
from services.ms4_orchestrator.models import ItemEnrichment, Status, ProposalStatus


async def procesar_lote_v3():
    print("=================================================================")
    print("Iniciando Pipeline de Enriquecimiento y Clasificación V3.0 (Microservicios)")
    print("=================================================================")

    # 1. Asegurar tablas y catálogos iniciales
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    orchestrator = MS4Orchestrator()

    try:
        run_full_seeding(db)

        # 2. Obtener lista de publicaciones en ItemEnrichment
        items_a_procesar = db.query(ItemEnrichment).all()

        # Si aún no hay registros, insertar lote de prueba representativo
        if not items_a_procesar:
            print("[*] Base de datos limpia: Insertando registros de prueba...")
            test_dois = [
                ("item-uuid-001", "10.1177/16878140211010657", "Analysis of medical images using deep learning"),
                ("item-uuid-002", "10.1016/j.robot.2024.104661", "Adaptive robotics in manufacturing systems"),
                ("item-uuid-003", "10.1155/2020/7816785", "Machine Learning in Solar and Wind Renewable Energy"),
                ("item-uuid-004", "10.3390/ijms21217922", "Molecular Mechanisms of Plant Tolerance to Drought"),
                ("item-uuid-005", "10.5354/0719-2584.2025.74613", "Políticas públicas y educación superior en Chile")
            ]
            for uuid_dsp, doi_val, tit_val in test_dois:
                orchestrator.handle_detection(
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
            print("-----------------------------------------------------------------")
            print(f"Ítem UUID DSpace: {item.uuid_dspace}")
            print(f"DOI: {item.doi} | Título: {item.title}")
            print(f"Estado Inicial: {st_name}")

            # 3.1 Idempotencia temprana: saltar si ya está en curaduría, exportado o cerrado
            if st_name in [
                ProposalStatus.EN_REVISION, ProposalStatus.APROBADA,
                ProposalStatus.EXPORTADA, ProposalStatus.CARGADA,
                ProposalStatus.CERRADA
            ]:
                print(f"[SKIP] Omitido por Idempotencia Temprana (Estado activo: {st_name}).")
                continue

            # 3.2 Ejecutar pipeline coordinado por el Orquestador MS4
            print("[*] Ejecutando Pipeline en Microservicios MS1 (Recuperación) y MS2 (Clasificación)...")
            res_pipeline = await orchestrator.run_pipeline_for_item(db, item)
            print(f"  -> Resultado de orquestación: {res_pipeline.get('status')}")

            # Refrescar estado final
            db.refresh(item)
            final_status = item.status.name if item.status else "Desconocido"
            print(f"[✔] Proceso completado. Estado final del ítem: {final_status}")

    except Exception as e:
        print(f"[X] Error crítico en el pipeline: {e}")
    finally:
        db.close()
        print("\n=================================================================")
        print("Pipeline V3 finalizado exitosamente.")
        print("=================================================================")


if __name__ == "__main__":
    asyncio.run(procesar_lote_v3())
