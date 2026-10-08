from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional
from urllib.parse import quote
import httpx


@dataclass
class MetadataResponse:
    title: str
    authors: List[str] = field(default_factory=list)
    doi: Optional[str] = None
    year: Optional[int] = None
    source: str = "openalex"
    url: Optional[str] = None
    abstract: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    funding_source: Optional[List[str]] = None
    ods: Optional[List[str]] = None
    derechos_acceso: str = "Desconocido"


class OpenAlexClient:
    """
    Cliente optimizado de OpenAlex para Agentes de IA y repositorios DSpace-CRIS.
    Maneja el 'Polite Pool', des-indexación de abstracts, fuzzy matching y extracción de metadatos.
    """

    def __init__(self, email: str, timeout: float = 10.0):
        self.email = email
        self.timeout = timeout
        self.headers = {
            "User-Agent": f"DSpaceCRIS-Agent/1.0 (mailto:{self.email})"
        }
        self.base_url = "https://api.openalex.org/works"

    async def get_by_doi(
        self, doi: str, client: httpx.AsyncClient
    ) -> Optional[MetadataResponse]:
        """Recupera metadatos exactos de una publicación a partir de su DOI."""
        clean_doi = doi.replace("https://doi.org/", "").strip()
        encoded_doi = quote(clean_doi, safe="")
        url = f"{self.base_url}/doi:{encoded_doi}"

        try:
            response = await client.get(
                url, headers=self.headers, timeout=self.timeout
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return self._parse_openalex_item(response.json())
        except Exception as e:
            print(f"[OpenAlex] Error recuperando DOI '{doi}': {e}")
            return None

    async def get_doi_by_title_and_abstract(
        self,
        title: Optional[str] = None,
        abstract: Optional[str] = None,
        client: Optional[httpx.AsyncClient] = None,
        similarity_threshold: float = 0.85,
    ) -> Optional[str]:
        """
        Busca el DOI de una publicación dada una coincidencia por título/abstract.
        Aplica Fuzzy Matching para prevenir falsos positivos antes de retornar el DOI.
        """
        if not title and not abstract:
            return None

        local_client = client or httpx.AsyncClient()
        params: Dict[str, Any] = {
            "per-page": 5,
            "mailto": self.email,
        }

        if title:
            params["filter"] = f"title.search:{title}"
        elif abstract:
            params["search"] = abstract[:300]

        try:
            response = await local_client.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            results = response.json().get("results", [])

            for candidate in results:
                candidate_title = candidate.get("title") or ""

                if title:
                    score = self._calculate_similarity(title, candidate_title)
                    if score < similarity_threshold:
                        continue  # Salta si la similitud no supera el umbral

                retrieved_doi = candidate.get("doi")
                if retrieved_doi:
                    return retrieved_doi.replace("https://doi.org/", "").strip()

        except Exception as e:
            print(f"[OpenAlex] Error buscando DOI por título/abstract: {e}")
        finally:
            if not client:
                await local_client.aclose()

        return None

    async def search_candidates_by_title(
        self,
        title: str,
        year: Optional[int] = None,
        client: Optional[httpx.AsyncClient] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Devuelve una lista de candidatos procesados junto a su Score de Similitud
        para la etapa de evaluación o decisión en el Agente de IA.
        """
        local_client = client or httpx.AsyncClient()
        params: Dict[str, Any] = {
            "search": title,
            "per-page": limit,
            "mailto": self.email,
        }

        if year:
            params["filter"] = f"publication_year:{year - 1}-{year + 1}"

        candidates = []
        try:
            response = await local_client.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            results = response.json().get("results", [])

            for item in results:
                candidate_title = item.get("title") or ""
                similarity_score = self._calculate_similarity(
                    title, candidate_title
                )
                parsed_metadata = self._parse_openalex_item(item)

                candidates.append(
                    {
                        "similarity_score": round(similarity_score, 4),
                        "metadata": parsed_metadata,
                        "raw_item": item,
                    }
                )

            # Ordenar candidatos de mayor a menor similitud
            candidates.sort(key=lambda x: x["similarity_score"], reverse=True)

        except Exception as e:
            print(f"[OpenAlex] Error buscando candidatos por título: {e}")
        finally:
            if not client:
                await local_client.aclose()

        return candidates

    def _parse_openalex_item(self, item: Dict[str, Any]) -> MetadataResponse:
        """Extrae y normaliza los metadatos desde el JSON de OpenAlex."""
        title = item.get("title") or "Sin título"

        authors = [
            auth.get("author", {}).get("display_name", "")
            for auth in item.get("authorships", [])
        ]
        authors = [a for a in authors if a]

        retrieved_doi = item.get("doi")
        if retrieved_doi and retrieved_doi.startswith("https://doi.org/"):
            retrieved_doi = retrieved_doi.replace("https://doi.org/", "")

        year = item.get("publication_year")
        item_url = item.get("id")

        abstract = self._reconstruct_abstract(
            item.get("abstract_inverted_index")
        )

        keywords = []
        if item.get("keywords"):
            keywords = [
                kw.get("display_name")
                for kw in item.get("keywords", [])
                if kw.get("display_name")
            ]

        funding_source = []
        for grant in item.get("grants", []):
            funder = grant.get("funder_display_name")
            if funder:
                funding_source.append(funder)
        funding_source = (
            list(dict.fromkeys(funding_source)) if funding_source else None
        )

        ods = []
        for sdg in item.get("sustainable_development_goals", []):
            if sdg.get("display_name"):
                ods.append(sdg.get("display_name"))
        ods = list(dict.fromkeys(ods)) if ods else None

        is_oa = item.get("open_access", {}).get("is_oa")
        derechos_acceso = (
            "Abierto"
            if is_oa is True
            else ("Cerrado" if is_oa is False else "Desconocido")
        )

        return MetadataResponse(
            title=title,
            authors=authors,
            doi=retrieved_doi,
            year=year,
            source="openalex",
            url=item_url,
            abstract=abstract,
            keywords=keywords,
            funding_source=funding_source,
            ods=ods,
            derechos_acceso=derechos_acceso,
        )

    @staticmethod
    def _reconstruct_abstract(
        inverted_index: Optional[Dict[str, List[int]]]
    ) -> Optional[str]:
        """Reconstruye el Abstract de OpenAlex partiendo del formato inverted_index."""
        if not inverted_index:
            return None

        word_positions = []
        for word, positions in inverted_index.items():
            for pos in positions:
                word_positions.append((pos, word))

        word_positions.sort(key=lambda x: x[0])
        return " ".join(word for _, word in word_positions)

    @staticmethod
    def _calculate_similarity(a: str, b: str) -> float:
        """Calcula el ratio de similitud básica entre dos cadenas de texto."""
        if not a or not b:
            return 0.0
        return SequenceMatcher(
            None, a.lower().strip(), b.lower().strip()
        ).ratio()
