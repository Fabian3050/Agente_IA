import asyncio
import sys
import os

# Asegurar que la ruta base esté en el sys.path para importaciones absolutas
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.db_models import DoiRecord, DocumentMetadata
from app.services.classification_service import ClassificationService
from app.clients.openalex_client import get_by_doi_openalex

async def procesar_lote():
    print("Iniciando procesamiento de DOIs por lotes...")
    db = SessionLocal()
    classification_service = ClassificationService()

    try:
        # Obtener todos los DOIs
        todos_los_dois = db.query(DoiRecord).all()
        print(f"Total de registros a procesar: {len(todos_los_dois)}")

        for registro in todos_los_dois:
            print(f"\n--- Procesando DOI: {registro.doi} (ID: {registro.id}) ---")
            
            # 1. Comprobar si ya existe en DocumentMetadata (usando el mismo ID)
            existe = db.query(DocumentMetadata).filter(DocumentMetadata.id == registro.id).first()
            if existe:
                print(f"[-] El DOI {registro.doi} ya fue procesado y guardado. Saltando...")
                continue

            # 2. Consultar OpenAlex
            print("[*] Consultando a OpenAlex...")
            metadata = await get_by_doi_openalex(registro.doi)

            if not metadata:
                print(f"[!] No se encontraron metadatos en OpenAlex para {registro.doi}. Guardando como vacío.")
                nuevo_doc = DocumentMetadata(
                    id=registro.id,
                    titulo="No encontrado",
                    resumen=None,
                    palabras_clave=None,
                    derechos_acceso=None,
                    fuente_financiamiento=None,
                    area_oce=None,
                    area_ods=None
                )
                db.add(nuevo_doc)
                db.commit()
                continue

            # Formatear campos simples
            titulo = metadata.title
            resumen = metadata.abstract
            palabras_clave = ", ".join(metadata.keywords) if metadata.keywords else None
            derechos_acceso = metadata.derechos_acceso
            fuente_financiamiento = ", ".join(metadata.funding_source) if metadata.funding_source else None

            # 3. Clasificación con Llama 3.2 (OCDE y ODS)
            area_oce_str = None
            area_ods_str = None

            try:
                print("[*] Clasificando OCDE mediante LLM...")
                ocde_res = await classification_service.classify_metadata_ocde(metadata)
                if ocde_res.clasificaciones:
                    area_oce_str = ", ".join([f"{c.codigo_ocde} ({c.area_ocde})" for c in ocde_res.clasificaciones])
            except Exception as e:
                print(f"[!] Error clasificando OCDE: {e}")
                area_oce_str = "Error en clasificación"

            try:
                print("[*] Clasificando ODS mediante LLM...")
                ods_res = await classification_service.classify_metadata_ods(metadata)
                if ods_res.clasificaciones:
                    area_ods_str = ", ".join([f"ODS {c.numero_ods} ({c.nombre_ods})" for c in ods_res.clasificaciones])
            except Exception as e:
                print(f"[!] Error clasificando ODS: {e}")
                area_ods_str = "Error en clasificación"

            # 4. Guardar en la base de datos
            nuevo_doc = DocumentMetadata(
                id=registro.id,
                titulo=titulo,
                resumen=resumen,
                palabras_clave=palabras_clave,
                derechos_acceso=derechos_acceso,
                fuente_financiamiento=fuente_financiamiento,
                area_oce=area_oce_str,
                area_ods=area_ods_str
            )
            db.add(nuevo_doc)
            db.commit()
            print(f"[+] Registro guardado exitosamente.")

    except Exception as e:
        print(f"Error crítico en el proceso batch: {e}")
    finally:
        db.close()
        print("\nProceso finalizado.")

if __name__ == "__main__":
    asyncio.run(procesar_lote())
