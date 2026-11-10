import asyncio
from typing import List, Optional
from models.metadata_model import MetadataResponse
from clients.crossref_client import search_crossref, get_by_doi_crossref, get_doi_by_title_and_abstract_crossref
from clients.openalex_client import OpenAlexClient
import httpx
from clients.semantic_scholar_client import search_semantic_scholar, get_by_doi_semantic_scholar, get_doi_by_title_and_abstract_semantic_scholar
from clients.europe_pmc_client import search_europe_pmc, get_by_doi_europe_pmc, get_doi_by_title_and_abstract_europe_pmc
from clients.unpaywall_client import search_unpaywall, get_metadata_by_doi_unpaywall

class MetadataService:
    def __init__(self):
        self.openalex_client = OpenAlexClient(email="agente_ia_vriic@usach.cl")

    async def _search_openalex_wrapper(self, query: str, limit: int) -> List[MetadataResponse]:
        candidates = await self.openalex_client.search_candidates_by_title(title=query, limit=limit)
        results = []
        for c in candidates:
            m = c["metadata"]
            results.append(m)
        return results

    async def _get_by_doi_openalex_wrapper(self, doi: str) -> Optional[MetadataResponse]:
        async with httpx.AsyncClient() as client:
            return await self.openalex_client.get_by_doi(doi, client)

    async def search_metadata(self, query: str, source: Optional[str] = None, limit: int = 5) -> List[MetadataResponse]:
        source_functions = {
            "crossref": search_crossref,
            "openalex": self._search_openalex_wrapper,
            "semanticscholar": search_semantic_scholar,
            "europepmc": search_europe_pmc,
            "unpaywall": search_unpaywall
        }

        if source:
            source_lower = source.lower()
            if source_lower not in source_functions:
                raise ValueError(f"Fuente desconocida: {source}. Fuentes disponibles: {list(source_functions.keys())}")
            func = source_functions[source_lower]
            return await func(query, limit)

        tasks = [func(query, limit) for func in source_functions.values()]
        results_nested = await asyncio.gather(*tasks, return_exceptions=True)

        combined_results = []
        for res in results_nested:
            if isinstance(res, list):
                combined_results.extend(res)
            elif isinstance(res, Exception):
                print(f"Error en una de las fuentes concurrentes: {res}")

        return combined_results

    async def get_metadata_by_doi(self, doi: str, source: Optional[str] = None) -> List[MetadataResponse]:
        source_functions = {
            "crossref": get_by_doi_crossref,
            "openalex": self._get_by_doi_openalex_wrapper,
            "semanticscholar": get_by_doi_semantic_scholar,
            "europepmc": get_by_doi_europe_pmc,
            "unpaywall": get_metadata_by_doi_unpaywall
        }

        if source:
            source_lower = source.lower()
            if source_lower not in source_functions:
                raise ValueError(f"Fuente desconocida: {source}. Fuentes disponibles: {list(source_functions.keys())}")
            func = source_functions[source_lower]
            res = await func(doi)
            return [res] if res else []

        tasks = [func(doi) for func in source_functions.values()]
        results_nested = await asyncio.gather(*tasks, return_exceptions=True)

        combined_results = []
        for res in results_nested:
            if isinstance(res, MetadataResponse) and res is not None:
                combined_results.append(res)
            elif isinstance(res, Exception):
                print(f"Error consultando DOI en una de las fuentes: {res}")

        return combined_results

