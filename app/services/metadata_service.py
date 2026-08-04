import asyncio
from typing import List, Optional
from app.models.metadata_model import MetadataResponse
from app.clients.crossref_client import search_crossref, get_by_doi_crossref
from app.clients.openalex_client import search_openalex, get_by_doi_openalex
from app.clients.semantic_scholar_client import search_semantic_scholar, get_by_doi_semantic_scholar
from app.clients.europe_pmc_client import search_europe_pmc, get_by_doi_europe_pmc

class MetadataService:
    async def search_metadata(self, query: str, source: Optional[str] = None, limit_per_source: int = 5) -> List[MetadataResponse]:
        """
        Busca metadatos. Si 'source' es especificado, busca solo en ese proveedor.
        Si 'source' es None, busca en todos concurrentemente.
        """
        results = []
        
        if source:
            source = source.lower()
            if source == "crossref":
                results.extend(await search_crossref(query, limit_per_source))
            elif source == "openalex":
                results.extend(await search_openalex(query, limit_per_source))
            elif source == "semanticscholar":
                results.extend(await search_semantic_scholar(query, limit_per_source))
            elif source == "europepmc":
                results.extend(await search_europe_pmc(query, limit_per_source))
        else:
            # Búsqueda concurrente en todos los clientes
            tasks = [
                search_crossref(query, limit_per_source),
                search_openalex(query, limit_per_source),
                search_semantic_scholar(query, limit_per_source),
                search_europe_pmc(query, limit_per_source)
            ]
            
            completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
            
            for task_result in completed_tasks:
                if isinstance(task_result, list):
                    results.extend(task_result)
                else:
                    # En caso de excepción no controlada en algún cliente
                    print(f"Error en tarea concurrente: {task_result}")
                    
        return results

    async def get_metadata_by_doi(self, doi: str, source: Optional[str] = None) -> List[MetadataResponse]:
        """
        Busca metadatos específicamente por DOI.
        """
        results = []
        
        if source:
            source = source.lower()
            if source == "crossref":
                res = await get_by_doi_crossref(doi)
                if res: results.append(res)
            elif source == "openalex":
                res = await get_by_doi_openalex(doi)
                if res: results.append(res)
            elif source == "semanticscholar":
                res = await get_by_doi_semantic_scholar(doi)
                if res: results.append(res)
            elif source == "europepmc":
                res = await get_by_doi_europe_pmc(doi)
                if res: results.append(res)
        else:
            tasks = [
                get_by_doi_crossref(doi),
                get_by_doi_openalex(doi),
                get_by_doi_semantic_scholar(doi),
                get_by_doi_europe_pmc(doi)
            ]
            
            completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
            
            for task_result in completed_tasks:
                if isinstance(task_result, MetadataResponse):
                    results.append(task_result)
                elif isinstance(task_result, Exception):
                    print(f"Error en tarea concurrente por DOI: {task_result}")
                    
        return results
