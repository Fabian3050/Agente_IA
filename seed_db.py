"""
Script de inicialización de la base de datos (Seeding).
Crea las 13 tablas relacionales en Tercera Forma Normal (3NF) y puebla
los catálogos oficiales parametrizados (Status, ExternalAPISource, Roles y Categorías OCDE/ODS).
"""
import sys
import os

# Asegurar que la ruta base esté en sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base, SessionLocal
from app.services.seed_service import run_full_seeding
from app.models.db_models import ItemEnrichment, Status, ProposalStatus

def main():
    print("==========================================================")
    print("Inicializando Base de Datos - Agente IA DSpace-CRIS V3.0")
    print("==========================================================")

    # 1. Crear todas las tablas en la BD
    print("[*] Creando tablas relacionales en la base de datos...")
    Base.metadata.create_all(bind=engine)
    print("[+] Tablas creadas exitosamente.")

    # 2. Poblar catálogos oficiales
    db = SessionLocal()
    try:
        print("[*] Sembrando catálogos oficiales (Status, Fuentes, Roles, Categorías OCDE/ODS)...")
        results = run_full_seeding(db)
        print(f"  -> Estados creados: {results['statuses_created']}")
        print(f"  -> Fuentes creadas: {results['external_sources_created']}")
        print(f"  -> Roles creados: {results['roles_created']}")
        print(f"  -> Categorías OCDE/ODS creadas: {results['categories_created']}")

        # 3. Opcional: Insertar publicaciones de prueba si no existen
        status_detectada = db.query(Status).filter(Status.name == ProposalStatus.DETECTADA).first()
        if not status_detectada:
            raise Exception("Estado 'Detectada' no encontrado tras el seeding.")

        dois_de_prueba = [
            ("uuid-test-001", "10.1177/16878140211010657", "A review on deep learning in medical image analysis"),
            ("uuid-test-002", "10.1016/j.robot.2024.104661", "Adaptive robotic manipulation under uncertainty"),
            ("uuid-test-003", "10.1155/2020/7816785", "Machine Learning Approaches in Renewable Energy Systems"),
            ("uuid-test-004", "10.3390/ijms21217922", "Molecular Insights into Plant Stress Tolerance"),
            ("uuid-test-005", "10.5354/0719-2584.2025.74613", "Estudios sobre gobernanza universitaria en Chile")
        ]

        inserted_items = 0
        for uuid_dspace, doi, title in dois_de_prueba:
            existente = db.query(ItemEnrichment).filter(ItemEnrichment.uuid_dspace == uuid_dspace).first()
            if not existente:
                item = ItemEnrichment(
                    uuid_dspace=uuid_dspace,
                    doi=doi,
                    title=title,
                    id_status=status_detectada.id
                )
                db.add(item)
                inserted_items += 1

        db.commit()
        if inserted_items > 0:
            print(f"Se insertaron {inserted_items} publicaciones de prueba en estado 'Detectada'.")
        print("\nBase de datos inicializada y lista para operar.")

    except Exception as e:
        db.rollback()
        print(f"Error durante la inicialización: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
