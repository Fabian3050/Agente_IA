import asyncio
import sys
import os

# Asegurar que la ruta base esté en el sys.path para importaciones absolutas
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.db_models import DoiRecord, DocumentMetadata
from app.services.classification_service import ClassificationService
from app.clients.openalex_client import get_by_doi_openalex
from app.clients.crossref_client import get_by_doi_crossref
from app.clients.semantic_scholar_client import get_by_doi_semantic_scholar

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

            # 2. Consultar Metadatos en cascada (OpenAlex -> CrossRef -> Semantic Scholar)
            print("[*] Consultando fuentes de metadatos...")
            
            titulo = None
            resumen = None
            palabras_clave = None
            derechos_acceso = None
            fuente_financiamiento = None
            
            fuentes = [
                ("OpenAlex", get_by_doi_openalex),
                ("CrossRef", get_by_doi_crossref),
                ("Semantic Scholar", get_by_doi_semantic_scholar)
            ]
            
            metadata_clasificacion = None

            for nombre_fuente, func_fuente in fuentes:
                # Si todos los campos requeridos ya fueron obtenidos, no consultamos más
                if titulo and resumen and palabras_clave and derechos_acceso and fuente_financiamiento:
                    break
                    
                print(f"  -> Consultando {nombre_fuente}...")
                try:
                    metadata = await func_fuente(registro.doi)
                except Exception as e:
                    print(f"  [X] Error al consultar {nombre_fuente}: {e}")
                    metadata = None
                
                if metadata:
                    if not metadata_clasificacion:
                        metadata_clasificacion = metadata
                        
                    if not titulo and metadata.title and metadata.title != "No title":
                        titulo = metadata.title
                    if not resumen and metadata.abstract:
                        resumen = metadata.abstract
                    if not palabras_clave and metadata.keywords:
                        palabras_clave = ", ".join(metadata.keywords)
                    if not derechos_acceso and metadata.derechos_acceso:
                        derechos_acceso = metadata.derechos_acceso
                    if not fuente_financiamiento and metadata.funding_source:
                        fuente_financiamiento = ", ".join(metadata.funding_source)

            # Verificar información faltante
            faltantes = []
            if not titulo: faltantes.append("titulo")
            if not resumen: faltantes.append("resumen")
            if not palabras_clave: faltantes.append("palabras_clave")
            if not derechos_acceso: faltantes.append("derechos_acceso")
            if not fuente_financiamiento: faltantes.append("fuente_financiamiento")
            
            if faltantes:
                print(f"[!] Metadatos incompletos para {registro.doi}. Faltan las siguientes columnas: {', '.join(faltantes)}")

            if not titulo:
                titulo = "No encontrado"

            # 3. Clasificación con LLM (OCDE y ODS)
            area_oce_str = None
            area_ods_str = None

            if metadata_clasificacion:
                # Asegurar que el objeto a clasificar tenga el título y resumen más completos que encontramos
                metadata_clasificacion.title = titulo if titulo != "No encontrado" else metadata_clasificacion.title
                metadata_clasificacion.abstract = resumen if resumen else metadata_clasificacion.abstract
                
                try:
                    print("[*] Clasificando OCDE mediante LLM...")
                    ocde_res = await classification_service.classify_metadata_ocde(metadata_clasificacion)
                    if ocde_res.clasificaciones:
                        area_oce_str = ", ".join([f"{c.codigo_ocde} ({c.area_ocde})" for c in ocde_res.clasificaciones])
                except Exception as e:
                    print(f"[!] Error clasificando OCDE: {e}")
                    area_oce_str = "Error en clasificación"

                try:
                    print("[*] Clasificando ODS mediante LLM...")
                    ods_res = await classification_service.classify_metadata_ods(metadata_clasificacion)
                    if ods_res.clasificaciones:
                        area_ods_str = ", ".join([f"ODS {c.numero_ods} ({c.nombre_ods})" for c in ods_res.clasificaciones])
                except Exception as e:
                    print(f"[!] Error clasificando ODS: {e}")
                    area_ods_str = "Error en clasificación"
            else:
                print(f"[!] No se obtuvo ningún metadato base para clasificar con LLM el DOI {registro.doi}")

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
