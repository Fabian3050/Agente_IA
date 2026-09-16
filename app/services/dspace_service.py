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
    
    async def get_all_items(self, page: int = 0, size: int = 20):
        """
        Obtiene ítems del repositorio con paginación.
        Para obtener TODO el repositorio de verdad, tendrías que iterar sobre las páginas,
        ya que DSpace limita los resultados por página (ej. 20 por defecto).
        """
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
        
        return {
            "items": items,
            "page_info": search_result.get("page", {}) # Info útil de total de páginas, etc.
        }

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

        return {
            "uuid": indexable_object.get("id"),
            "title": get_metadata_value("dc.title", "Sin título"),
            "abstract": get_metadata_value("dc.description.abstract", "No disponible"),
            "doi": get_metadata_value("dc.identifier.doi", "No disponible"),
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
        total_missing_abs = 0
        total_missing_doi = 0
        uuids_sin_abstract = []
        uuids_sin_doi = []

        def procesar_items(items):
            revisados_pag = len(items)
            missing_abs_pag = 0
            missing_doi_pag = 0
            uuids_abs_pag = []
            uuids_doi_pag = []
            
            for item in items:
                if item.get("abstract") == "" or item.get("abstract") == "Sin resumen" or item.get("abstract") == "[No abstract available]":
                    missing_abs_pag += 1
                    uuids_abs_pag.append(item.get("uuid"))
                if item.get("doi") == "No disponible" or item.get("doi") == "":
                    missing_doi_pag += 1
                    uuids_doi_pag.append(item.get("uuid"))
                    
            return revisados_pag, missing_abs_pag, missing_doi_pag, uuids_abs_pag, uuids_doi_pag

        # Procesamos la página 0
        rev, miss_abs, miss_doi, uuids_abs, uuids_doi = procesar_items(resultado_inicial.get("items", []))
        total_revisados += rev
        total_missing_abs += miss_abs
        total_missing_doi += miss_doi
        uuids_sin_abstract.extend(uuids_abs)
        uuids_sin_doi.extend(uuids_doi)

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
                        return 0, 0, 0, [], []

            # Tareas para el resto de las páginas
            tareas = [fetch_and_process_page(p) for p in range(1, total_pages)]
            
            resultados_paginas = await asyncio.gather(*tareas)

            # Sumamos resultados
            for rev, miss_abs, miss_doi, uuids_abs, uuids_doi in resultados_paginas:
                total_revisados += rev
                total_missing_abs += miss_abs
                total_missing_doi += miss_doi
                uuids_sin_abstract.extend(uuids_abs)
                uuids_sin_doi.extend(uuids_doi)

        return {
            "total_revisados": total_revisados,
            "total_sin_abstract": total_missing_abs,
            "total_sin_doi": total_missing_doi,
            "uuids_sin_abstract": uuids_sin_abstract,
            "uuids_sin_doi": uuids_sin_doi
        }