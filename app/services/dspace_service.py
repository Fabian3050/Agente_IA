from app.clients.dspace_auth_client import DSpaceAuthClient
import asyncio

class DSpaceService:
    def __init__(self):
        self.client = DSpaceAuthClient()
        self.token = None # Aquí guardaremos el token para no pedirlo en cada consulta
        
    async def _ensure_authenticated(self):
        """Helper para autenticarse solo si no tenemos un token activo."""
        if not self.token:
            self.token = await self.client.authenticate()
            if not self.token:
                raise Exception("No se pudo obtener el token de DSpace. Revisa tus credenciales.")
    
    async def get_all_items(self, page: int = 0, size: int = 20, use_cache: bool = True):
        """
        Obtiene ítems del repositorio con paginación.
        Implementa una caché local en disco para no saturar la API ni la RAM.
        """
        import os
        import json
        
        cache_dir = "cache_dspace"
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
            
        cache_file = os.path.join(cache_dir, f"page_{page}_size_{size}.json")
        
        # 1. Intentamos leer desde la caché en disco
        if use_cache and os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
                
        await self._ensure_authenticated()
        
        # Le pasamos parámetros de paginación y filtros al cliente
        params = {
            "page": page,
            "size": size,
            "f.entityType": "Publication,equals" # Filtramos para que solo traiga publicaciones reales
        }
        
        # Utilizamos el método get_items del cliente (apunta a /discover/search/objects)
        data = await self.client.get_items(self.token, query_params=params)
        
        # La API de Discover tiene una estructura anidada diferente a /core/items
        search_result = data.get("_embedded", {}).get("searchResult", {})
        
        # Obtenemos los ítems crudos (objects)
        raw_items = search_result.get("_embedded", {}).get("objects", [])
        
        # Parseamos y limpiamos los ítems
        items = [self._parse_item(item) for item in raw_items]
        
        result = {
            "items": items,
            "page_info": search_result.get("page", {}) # Info útil de total de páginas, etc.
        }
        
        # 2. Guardamos el resultado en disco
        if use_cache:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
                
        return result

    def _parse_item(self, item: dict) -> dict:
        """Extrae de forma limpia los metadatos más importantes de un registro de DSpace."""
        indexable_object = item.get("_embedded", {}).get("indexableObject", {})
        metadata = indexable_object.get("metadata", {})
        
        # Función auxiliar para sacar el primer valor de una lista de metadatos de DSpace
        def get_metadata_value(field: str, default: str = None):
            values = metadata.get(field, [])
            if values and len(values) > 0:
                val = values[0].get("value")
                # Verificamos que 'val' no sea nulo ni un texto en blanco
                if val is not None and str(val).strip():
                    return str(val).strip()
            return default

        # Función auxiliar para sacar todos los valores de una lista de metadatos (útil para palabras clave/subjects)
        def get_metadata_values_list(field: str):
            values = metadata.get(field, [])
            return [str(v.get("value")).strip() for v in values if v.get("value") is not None and str(v.get("value")).strip()]

        return {
            "uuid": indexable_object.get("id"),
            "title": get_metadata_value("dc.title", "Sin título"),
            "abstract": get_metadata_value("dc.description.abstract", "No disponible"),
            "doi": get_metadata_value("dc.identifier.doi", "No disponible"),
            "type": get_metadata_value("dc.type", "No disponible"),
            "oaire_resourcetype": get_metadata_value("oaire.resourceType", "No disponible"),
            "keywords": get_metadata_values_list("dc.subject"), # Puede tener múltiples valores
            "uri": get_metadata_value("dc.identifier.uri"), # Link público usualmente
            "all_metadata": metadata
        }
        
    async def get_metadata(self, identifier: str):
        """
        Obtiene los metadatos de un ID en específico (UUID).
        Busca a través de todas las páginas de resultados en paralelo
        para encontrar el registro, dado que el filtrado de la API 
        no lo encuentra directamente en esta instancia.
        """
        await self._ensure_authenticated()
        
        size = 100
        params = {
            "page": 0,
            "size": size,
            "dsoType": "item"
        }
        
        # Función auxiliar para buscar el UUID dentro de los raw items de una página
        def encontrar_raw_item(raw_items_list):
            for raw_item in raw_items_list:
                indexable_object = raw_item.get("_embedded", {}).get("indexableObject", {})
                item_id = indexable_object.get("id")
                item_uuid = indexable_object.get("uuid")
                if identifier in (item_id, item_uuid):
                    return raw_item
            return None
            
        # 1. Buscar en la primera página y obtener el total de páginas
        data = await self.client.get_items(self.token, query_params=params)
        search_result = data.get("_embedded", {}).get("searchResult", {})
        raw_items = search_result.get("_embedded", {}).get("objects", [])
        
        encontrado_raw = encontrar_raw_item(raw_items)
        if encontrado_raw:
            item_data = self._parse_item(encontrado_raw)
            item_data["all_metadata"] = encontrado_raw.get("_embedded", {}).get("indexableObject", {}).get("metadata", {})
            return item_data
            
        page_info = search_result.get("page", {})
        total_pages = page_info.get("totalPages", 1)
        
        # 2. Si hay más páginas, buscamos en paralelo
        if total_pages > 1:
            max_concurrent = 10 # Buscamos rápido de a 10 páginas
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def buscar_en_pagina(page_num):
                async with semaphore:
                    try:
                        p = {"page": page_num, "size": size, "dsoType": "item"}
                        d = await self.client.get_items(self.token, query_params=p)
                        sr = d.get("_embedded", {}).get("searchResult", {})
                        r_items = sr.get("_embedded", {}).get("objects", [])
                        return encontrar_raw_item(r_items)
                    except Exception as e:
                        print(f"Error procesando página {page_num} buscando UUID: {e}")
                        return None

            # Lanzamos tareas para las páginas restantes
            tareas = [asyncio.create_task(buscar_en_pagina(p)) for p in range(1, total_pages)]
            
            # as_completed nos permite reaccionar apenas una tarea termine
            for tarea in asyncio.as_completed(tareas):
                resultado_tarea = await tarea
                if resultado_tarea:
                    # Encontramos el ítem, cancelamos el resto de las tareas para no saturar
                    for t in tareas:
                        if not t.done():
                            t.cancel()
                    item_data = self._parse_item(resultado_tarea)
                    item_data["all_metadata"] = resultado_tarea.get("_embedded", {}).get("indexableObject", {}).get("metadata", {})
                    return item_data
                    
        return {"error": f"No se encontró ningún registro con el UUID {identifier} en todo el repositorio."}

    async def count_missing_metadata_optimized(self, size: int = 100, max_concurrent: int = 5, save_to_db: bool = False, db = None):
        """
        Recorre el repositorio en paralelo para máxima velocidad.
        Cuenta ítems sin abstract y sin DOI dentro de valid_resource_types.
        Opcionalmente guarda el histórico de métricas y la cola de enriquecimiento en base de datos.
        """
        print("Iniciando escaneo optimizado de metadatos faltantes...")
        
        # 1. Petición inicial
        resultado_inicial = await self.get_all_items(page=0, size=size)
        page_info = resultado_inicial.get("page_info", {})
        total_pages = page_info.get("totalPages", 1)
        
        print(f"Total de páginas a procesar: {total_pages} (a {size} ítems por página)")

        total_revisados = 0
        total_valid_resource_types = 0
        total_missing_title= 0
        total_missing_abs = 0
        total_no_abstract = 0
        total_missing_abs_org_art = 0
        total_missing_doi = 0
        total_missing_subjects = 0
        total_type_journal_Article = 0
        total_uuids_missing_abs_org_art = []
        total_uuids_pub_sin_doi_sin_abs = []
        total_distinct_oaire_types = set()
        total_pub_sin_doi_sin_abs = 0
        total_sin_abstract_con_doi = 0
        total_uuids_sin_abstract_con_doi = []
        total_sin_doi_ni_abstract = 0
        total_uuids_sin_doi_ni_abstract = []
        total_candidatos_enriquecimiento = []

        valid_resource_types = {
            "patente",
            "texto",
            "texto::artículo preliminar",
            "texto::contribución de congreso::actas de congreso::comunicación de congreso",
            #"texto::contribución de congreso::comunicación no publicada en actas de congreso",
            #"texto::contribución de congreso::presentación de congreso",
            "texto::informe",
            "texto::informe::estudio clínico",
            "texto::informe::informe técnico",
            "texto::libro::capítulo de libro",
            "texto::ponencia",
            "texto::revista::artículo",
            "texto::revista::artículo::artículo de revisión",
            "texto::revista::artículo::artículo original"
        }

        def procesar_items(items):
            revisados_pag = len(items)
            valid_resource_types_pag = 0
            missing_title_pag = 0
            missing_abs_pag = 0
            no_abstract_pag = 0
            missing_doi_pag = 0
            missing_subjects_pag = 0
            type_journal_Article_pag = 0
            missing_abs_org_art = 0
            pub_sin_doi_sin_abs = 0
            uuids_missing_abs_org_art = []
            uuids_pub_sin_doi_sin_abs = []
            distinct_oaire_pag = set()
            sin_abstract_con_doi_pag = 0
            uuids_sin_abstract_con_doi_pag = []
            sin_doi_ni_abstract_pag = 0
            uuids_sin_doi_ni_abstract_pag = []
            candidatos_pag = []
            
            for item in items:
                oaire_val = item.get("oaire_resourcetype")
                if oaire_val and oaire_val not in valid_resource_types:
                    distinct_oaire_pag.add(oaire_val)
                    
                # Solo procesar métricas y salidas para ítems dentro de valid_resource_types
                if oaire_val not in valid_resource_types:
                    continue

                valid_resource_types_pag += 1
                uuid = item.get("uuid")

                # Abstract
                abs_val = item.get("abstract")
                is_missing_abs = abs_val in ["No disponible", "", "Sin resumen"]
                is_no_abs_available = abs_val == "[No abstract available]"
                is_any_missing_abs = is_missing_abs or is_no_abs_available

                if is_missing_abs:
                    missing_abs_pag += 1
                    missing_abs_org_art += 1
                    uuids_missing_abs_org_art.append(uuid)

                if is_no_abs_available:
                    no_abstract_pag += 1

                # DOI
                doi_val = item.get("doi")
                is_missing_doi = doi_val in ["No disponible", "", None]
                has_doi = not is_missing_doi

                if is_missing_doi:
                    missing_doi_pag += 1

                # Title
                title_val = item.get("title")
                if title_val in ["No disponible", "", "Sin título", None]:
                    missing_title_pag += 1

                # Keywords / Subjects
                if not item.get("keywords"):
                    missing_subjects_pag += 1

                # Type
                if item.get("type") == "text::journal::journal article":
                    type_journal_Article_pag += 1

                # Sin abstract con DOI (dentro de valid_resource_types)
                if is_any_missing_abs and has_doi:
                    sin_abstract_con_doi_pag += 1
                    uuids_sin_abstract_con_doi_pag.append(uuid)

                # Sin DOI ni abstract (dentro de valid_resource_types)
                if is_any_missing_abs and is_missing_doi:
                    sin_doi_ni_abstract_pag += 1
                    uuids_sin_doi_ni_abstract_pag.append(uuid)
                    pub_sin_doi_sin_abs += 1
                    uuids_pub_sin_doi_sin_abs.append(uuid)

                # Si le falta abstract o DOI, es candidato para la cola de enriquecimiento
                if is_any_missing_abs or is_missing_doi:
                    falencia = (
                        "SIN_ABSTRACT_CON_DOI" if (is_any_missing_abs and has_doi) else
                        "SIN_DOI_NI_ABSTRACT" if (is_any_missing_abs and is_missing_doi) else
                        "SIN_DOI" if is_missing_doi else
                        "SIN_ABSTRACT"
                    )
                    candidatos_pag.append({
                        "dspace_uuid": uuid,
                        "doi": doi_val if has_doi else None,
                        "titulo": title_val if title_val not in ["No disponible", "", "Sin título", None] else None,
                        "tipo_recurso": oaire_val,
                        "tipo_falencia": falencia,
                        "resumen_original": abs_val if not is_any_missing_abs else None
                    })
                    
            return (
                revisados_pag, missing_title_pag, no_abstract_pag, missing_abs_pag, missing_abs_org_art,
                missing_doi_pag, missing_subjects_pag, type_journal_Article_pag, uuids_missing_abs_org_art,
                distinct_oaire_pag, pub_sin_doi_sin_abs, uuids_pub_sin_doi_sin_abs, sin_abstract_con_doi_pag,
                uuids_sin_abstract_con_doi_pag, sin_doi_ni_abstract_pag, uuids_sin_doi_ni_abstract_pag,
                valid_resource_types_pag, candidatos_pag
            )

        # Procesamos la página 0
        (
            rev, miss_title, no_abstract_pag, miss_abs, miss_abs_org_art, miss_doi, miss_subjects,
            type_journal_Article_pag, uuids_abs_org_art_pag0, dist_oaire_pag0, pub_sin_doi_sin_abs0,
            uuids_pub_sin_doi_sin_abs0, sin_abs_con_doi0, uuids_sin_abs_con_doi0, sin_doi_ni_abstract0,
            uuids_sin_doi_ni_abstract0, valid_res_pag0, cand_pag0
        ) = procesar_items(resultado_inicial.get("items", []))

        total_revisados += rev
        total_valid_resource_types += valid_res_pag0
        total_missing_title+= miss_title
        total_missing_abs += miss_abs
        total_no_abstract += no_abstract_pag
        total_missing_abs_org_art += miss_abs_org_art
        total_missing_doi += miss_doi
        total_missing_subjects += miss_subjects
        total_type_journal_Article += type_journal_Article_pag
        total_uuids_missing_abs_org_art.extend(uuids_abs_org_art_pag0)
        total_distinct_oaire_types.update(dist_oaire_pag0)
        total_pub_sin_doi_sin_abs += pub_sin_doi_sin_abs0
        total_uuids_pub_sin_doi_sin_abs.extend(uuids_pub_sin_doi_sin_abs0)
        total_sin_abstract_con_doi += sin_abs_con_doi0
        total_uuids_sin_abstract_con_doi.extend(uuids_sin_abs_con_doi0)
        total_sin_doi_ni_abstract += sin_doi_ni_abstract0
        total_uuids_sin_doi_ni_abstract.extend(uuids_sin_doi_ni_abstract0)
        total_candidatos_enriquecimiento.extend(cand_pag0)

        if total_pages > 1:
            semaphore = asyncio.Semaphore(max_concurrent)

            async def fetch_and_process_page(page_num):
                async with semaphore:
                    try:
                        print(f"Consultando página {page_num}/{total_pages - 1}...")
                        resultado = await self.get_all_items(page=page_num, size=size)
                        return procesar_items(resultado.get("items", []))
                    except Exception as e:
                        print(f"Error procesando página {page_num}: {e}")
                        return 0, 0, 0, 0, 0, 0, 0, 0, [], set(), 0, [], 0, [], 0, [], 0, []

            # Tareas para el resto de las páginas
            tareas = [fetch_and_process_page(p) for p in range(1, total_pages)]
            
            resultados_paginas = await asyncio.gather(*tareas)

            # Sumamos resultados
            for (
                rev, miss_title, no_abstract_pag, miss_abs, miss_abs_org_art, miss_doi, miss_subjects,
                type_journal_Article_pag, uuids_abs_org_art_pag, dist_oaire_pag, pub_sin_doi_sin_abs_pag,
                uuids_pub_sin_doi_sin_abs_pag, sin_abs_con_doi_pag, uuids_sin_abs_con_doi_pag,
                sin_doi_ni_abstract_pag, uuids_sin_doi_ni_abstract_pag, valid_res_pag, cand_pag
            ) in resultados_paginas:
                total_revisados += rev
                total_valid_resource_types += valid_res_pag
                total_missing_title+= miss_title
                total_no_abstract += no_abstract_pag
                total_missing_abs += miss_abs
                total_missing_abs_org_art += miss_abs_org_art
                total_missing_doi += miss_doi
                total_missing_subjects += miss_subjects
                total_type_journal_Article += type_journal_Article_pag
                total_uuids_missing_abs_org_art.extend(uuids_abs_org_art_pag)
                total_distinct_oaire_types.update(dist_oaire_pag)
                total_pub_sin_doi_sin_abs += pub_sin_doi_sin_abs_pag
                total_uuids_pub_sin_doi_sin_abs.extend(uuids_pub_sin_doi_sin_abs_pag)
                total_sin_abstract_con_doi += sin_abs_con_doi_pag
                total_uuids_sin_abstract_con_doi.extend(uuids_sin_abs_con_doi_pag)
                total_sin_doi_ni_abstract += sin_doi_ni_abstract_pag
                total_uuids_sin_doi_ni_abstract.extend(uuids_sin_doi_ni_abstract_pag)
                total_candidatos_enriquecimiento.extend(cand_pag)

        total_elements = page_info.get("totalElements")
        if total_elements is not None:
            total_revisados = total_elements

        resultado = {
            "total_revisados": total_revisados,
            "total_valid_resource_types": total_valid_resource_types,
            "total_sin_title": total_missing_title,
            "total_sin_abstract": total_missing_abs,
            "total_no_abstract_disponible": total_no_abstract,
            "total_missing_abs_org_art": total_missing_abs_org_art,
            "total_sin_doi": total_missing_doi,
            "total_sin_subjects": total_missing_subjects,
            "total_pub_sin_doi_sin_abs": total_pub_sin_doi_sin_abs,
            "total_sin_abstract_con_doi": total_sin_abstract_con_doi,
            "total_sin_doi_ni_abstract": total_sin_doi_ni_abstract,        
            "uuids_missing_abs_org_art": total_uuids_missing_abs_org_art,
            "uuids_pub_sin_doi_sin_abs": total_uuids_pub_sin_doi_sin_abs,
            "uuids_sin_abstract_con_doi": total_uuids_sin_abstract_con_doi,
            "uuids_sin_doi_ni_abstract": total_uuids_sin_doi_ni_abstract,
        }

        if save_to_db and db is not None:
            guardado_info = self.save_audit_and_queue(resultado, total_candidatos_enriquecimiento, db)
            resultado["db_guardado"] = guardado_info

        return resultado

    def save_audit_and_queue(self, resultado_metricas: dict, candidatos: list, db):
        """
        Persiste el snapshot histórico de métricas en DSpaceMetricsHistory
        y registra los ítems candidatos a enriquecer en DSpaceEnrichmentQueue.
        """
        from app.models.db_models import DSpaceMetricsHistory, DSpaceEnrichmentQueue

        # 1. Guardar Snapshot histórico
        snapshot = DSpaceMetricsHistory(
            total_revisados=resultado_metricas.get("total_revisados", 0),
            total_valid_resource_types=resultado_metricas.get("total_valid_resource_types", 0),
            total_sin_title=resultado_metricas.get("total_sin_title", 0),
            total_sin_abstract=resultado_metricas.get("total_sin_abstract", 0),
            total_no_abstract_disponible=resultado_metricas.get("total_no_abstract_disponible", 0),
            total_missing_abs_org_art=resultado_metricas.get("total_missing_abs_org_art", 0),
            total_sin_doi=resultado_metricas.get("total_sin_doi", 0),
            total_sin_subjects=resultado_metricas.get("total_sin_subjects", 0),
            total_pub_sin_doi_sin_abs=resultado_metricas.get("total_pub_sin_doi_sin_abs", 0),
            total_sin_abstract_con_doi=resultado_metricas.get("total_sin_abstract_con_doi", 0),
            total_sin_doi_ni_abstract=resultado_metricas.get("total_sin_doi_ni_abstract", 0),
        )
        db.add(snapshot)
        db.flush()

        # 2. Poblar cola de enriquecimiento evitando duplicados
        candidate_uuids = [c["dspace_uuid"] for c in candidatos if c.get("dspace_uuid")]
        existing_uuids = set()
        for i in range(0, len(candidate_uuids), 1000):
            batch = candidate_uuids[i:i+1000]
            rows = db.query(DSpaceEnrichmentQueue.dspace_uuid).filter(DSpaceEnrichmentQueue.dspace_uuid.in_(batch)).all()
            existing_uuids.update(r[0] for r in rows)

        new_items = []
        seen_uuids = set()
        for c in candidatos:
            uuid = c.get("dspace_uuid")
            if uuid and uuid not in existing_uuids and uuid not in seen_uuids:
                seen_uuids.add(uuid)
                new_items.append(DSpaceEnrichmentQueue(
                    dspace_uuid=uuid,
                    doi=c.get("doi"),
                    titulo=c.get("titulo"),
                    tipo_recurso=c.get("tipo_recurso"),
                    tipo_falencia=c.get("tipo_falencia"),
                    estado="PENDIENTE",
                    resumen_original=c.get("resumen_original")
                ))

        if new_items:
            db.bulk_save_objects(new_items)

        db.commit()

        return {
            "snapshot_id": snapshot.id,
            "total_candidatos_detectados": len(candidatos),
            "nuevos_en_cola": len(new_items),
            "ya_existentes_en_cola": len(seen_uuids & existing_uuids) if seen_uuids else 0
        }