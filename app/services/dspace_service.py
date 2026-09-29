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
            "uri": get_metadata_value("dc.identifier.uri") # Link público usualmente
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

    async def count_missing_metadata_optimized(self, size: int = 100, max_concurrent: int = 5):
        """
        Recorre el repositorio en paralelo para máxima velocidad.
        Cuenta ítems sin abstract y sin DOI.
        """
        print("Iniciando escaneo optimizado de metadatos faltantes...")
        
        # 1. Petición inicial
        resultado_inicial = await self.get_all_items(page=0, size=size)
        page_info = resultado_inicial.get("page_info", {})
        total_pages = page_info.get("totalPages", 1)
        
        print(f"Total de páginas a procesar: {total_pages} (a {size} ítems por página)")

        total_revisados = 0
        total_missing_title= 0
        total_missing_abs = 0
        total_no_abstract = 0
        total_missing_abs_org_art = 0
        total_missing_doi = 0
        total_missing_subjects = 0
        total_type_journal_Article = 0
        #total_distinct_journal_article = []
        #uuids_sin_abstract = []
        #uuids_sin_doi = []
        total_uuids_missing_abs_org_art = []
        total_uuids_pub_sin_doi_sin_abs = []
        total_distinct_oaire_types = set()
        total_pub_sin_doi_sin_abs = 0

        def procesar_items(items):
            revisados_pag = len(items)
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
            #uuids_abs_pag = []
            #uuids_doi_pag = []
            #uuids_distinct_journal_article_pag = []
            
            for item in items:
                if item.get("abstract") == "No disponible" or item.get("abstract") == "" or item.get("abstract") == "Sin resumen":
                    missing_abs_pag += 1
                    #uuids_abs_pag.append(item.get("uuid"))
                valid_resource_types = {
                    "patente",
                    "texto",
                    "texto::artículo preliminar",
                    "texto::contribución de congreso::actas de congreso::comunicación de congreso",
                    "texto::contribución de congreso::comunicación no publicada en actas de congreso",
                    "texto::contribución de congreso::presentación de congreso",
                    "texto::informe",
                    "texto::informe::estudio clínico",
                    "texto::informe::informe técnico",
                    "texto::libro::capítulo de libro",
                    "texto::ponencia",
                    "texto::revista::artículo",
                    "texto::revista::artículo::artículo de revisión",
                    "texto::revista::artículo::artículo original"
                }
                
                if (item.get("abstract") == "No disponible" or item.get("abstract") == "" or item.get("abstract") == "Sin resumen") and item.get("oaire_resourcetype") in valid_resource_types:
                    missing_abs_org_art += 1    
                    uuids_missing_abs_org_art.append(item.get("uuid"))
                if item.get("abstract") == "[No abstract available]":
                    no_abstract_pag += 1
                if item.get("doi") == "No disponible" or item.get("doi") == "":
                    missing_doi_pag += 1
                   # uuids_doi_pag.append(item.get("uuid"))
                if item.get("title") == "No disponible" or item.get("title") == "":
                    missing_title_pag += 1
                if not item.get("keywords"):
                    missing_subjects_pag += 1
                if item.get("type") == "text::journal::journal article":
                    type_journal_Article_pag += 1
                    
                oaire_val = item.get("oaire_resourcetype")
                if oaire_val and oaire_val not in valid_resource_types:
                    distinct_oaire_pag.add(oaire_val)
                if oaire_val and oaire_val not in valid_resource_types and (item.get("doi") == "No disponible" or item.get("doi") == "") and (item.get("abstract") == "No disponible" or item.get("abstract") == "" or item.get("abstract") == "Sin resumen"):
                    pub_sin_doi_sin_abs += 1
                    uuids_pub_sin_doi_sin_abs.append(item.get("uuid"))
                #else:
                 #   uuids_distinct_journal_article_pag.append(item.get("uuid"))
                    
            return revisados_pag, missing_title_pag, no_abstract_pag, missing_abs_pag, missing_abs_org_art, missing_doi_pag, missing_subjects_pag, type_journal_Article_pag, uuids_missing_abs_org_art, distinct_oaire_pag, pub_sin_doi_sin_abs, uuids_pub_sin_doi_sin_abs #uuids_abs_pag, uuids_doi_pag, uuids_distinct_journal_article_pag

        # Procesamos la página 0
        rev, miss_title, no_abstract_pag, miss_abs, miss_abs_org_art, miss_doi, miss_subjects, type_journal_Article_pag, uuids_abs_org_art_pag0, dist_oaire_pag0, pub_sin_doi_sin_abs0, uuids_pub_sin_doi_sin_abs0 = procesar_items(resultado_inicial.get("items", []))
        total_revisados += rev
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
        #total_distinct_journal_article.extend(uuids_distinct_journal)
        #uuids_sin_abstract.extend(uuids_abs)
        #uuids_sin_doi.extend(uuids_doi)

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
                        return 0, 0, 0, 0, 0, 0, 0, 0, [], set(), 0, [] #[], [], []

            # Tareas para el resto de las páginas
            tareas = [fetch_and_process_page(p) for p in range(1, total_pages)]
            
            resultados_paginas = await asyncio.gather(*tareas)

            # Sumamos resultados
            for rev, miss_title, no_abstract_pag, miss_abs, miss_abs_org_art, miss_doi, miss_subjects, type_journal_Article_pag, uuids_abs_org_art_pag, dist_oaire_pag, pub_sin_doi_sin_abs_pag, uuids_pub_sin_doi_sin_abs_pag in resultados_paginas:
                total_revisados += rev
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
                #total_distinct_journal_article.extend(uuids_distinct_journal)
                #uuids_sin_abstract.extend(uuids_abs)
                #uuids_sin_doi.extend(uuids_doi)

        return {
            "total_revisados": total_revisados,
            "total_sin_title": total_missing_title,
            "total_sin_abstract": total_missing_abs,
            "total_no_abstract_disponible": total_no_abstract,
            "total_missing_abs_org_art": total_missing_abs_org_art,
            "uuids_missing_abs_org_art": total_uuids_missing_abs_org_art,
            "distinct_oaire_resource_types": list(total_distinct_oaire_types),
            "total_sin_doi": total_missing_doi,
            "total_sin_subjects": total_missing_subjects,
            "total_type_journal_Article": total_type_journal_Article,
            "total_pub_sin_doi_sin_abs": total_pub_sin_doi_sin_abs,
            "uuids_pub_sin_doi_sin_abs": total_uuids_pub_sin_doi_sin_abs,
            #"uuids_distinct_journal_article": total_distinct_journal_article,
            #"uuids_sin_abstract": uuids_sin_abstract,
            #"uuids_sin_doi": uuids_sin_doi
        }