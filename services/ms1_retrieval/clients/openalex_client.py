from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional
from urllib.parse import quote
import httpx
from app.models.metadata_model import MetadataResponse
from app.clients.unpaywall_client import _normalize_oa_status, _normalize_version_type


class OpenAlexClient:
    """
    Cliente optimizado de OpenAlex para Agentes de IA y repositorios DSpace-CRIS.
    Maneja el 'Polite Pool', des-indexación de abstracts, fuzzy matching y separación
    entre palabras clave del autor y conceptos automáticos (cris.concept).
    """

    def __init__(self, email: str = "agente_ia_vriic@usach.cl", timeout: float = 10.0):
        self.email = email
        self.timeout = timeout
        self.headers = {
            "User-Agent": f"DSpaceCRIS-Agent/3.0 (mailto:{self.email})"
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
        """Extrae y normaliza los metadatos desde el JSON de OpenAlex según Sección 3.4."""
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

        # Palabras clave del autor (dc.subject)
        keywords = []
        if item.get("keywords"):
            keywords = [
                kw.get("display_name")
                for kw in item.get("keywords", [])
                if kw.get("display_name")
            ]

        # Conceptos automáticos algorítmicos (cris.concept)
        automated_concepts = []
        if item.get("concepts"):
            automated_concepts = [
                c.get("display_name")
                for c in item.get("concepts", [])
                if c.get("display_name")
            ]

        # Financiamiento desglosado
        funding_source = []
        funding_agency = None
        funding_id = None
        funding_grant_number = None

        grants = item.get("grants", [])
        if grants:
            first_grant = grants[0]
            funding_agency = first_grant.get("funder_display_name")
            funding_id = first_grant.get("funder")
            funding_grant_number = first_grant.get("award_id")

            for g in grants:
                funder = g.get("funder_display_name")
                if funder:
                    funding_source.append(funder)

        funding_source = list(dict.fromkeys(funding_source)) if funding_source else None

        ods = []
        for sdg in item.get("sustainable_development_goals", []):
            if sdg.get("display_name"):
                ods.append(sdg.get("display_name"))
        ods = list(dict.fromkeys(ods)) if ods else None

        oa_info = item.get("open_access", {})
        oa_status = _normalize_oa_status(oa_info.get("oa_status"))
        
        primary_loc = item.get("primary_location") or {}
        version_type = _normalize_version_type(primary_loc.get("version"))
        license_val = primary_loc.get("license")

        return MetadataResponse(
            title=title,
            authors=authors,
            doi=retrieved_doi,
            year=year,
            source="openalex",
            url=item_url,
            abstract=abstract,
            keywords=keywords,
            author_keywords=keywords,
            automated_concepts=automated_concepts,
            funding_source=funding_source,
            funding_agency=funding_agency,
            funding_id=funding_id,
            funding_grant_number=funding_grant_number,
            ods=ods,
            oa_status=oa_status,
            version_type=version_type,
            license=license_val,
            derechos_acceso=oa_status
        )

    @staticmethod
    def _reconstruct_abstract(
        inverted_index: Optional[Dict[str, List[int]]]
    ) -> Optional[str]:
        """Reconstruye sintácticamente el Abstract a partir del índice invertido de OpenAlex."""
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
        if not a or not b:
            return 0.0
        return SequenceMatcher(
            None, a.lower().strip(), b.lower().strip()
        ).ratio()


async def get_by_doi_openalex(doi: str, email: str = "agente_ia_vriic@usach.cl") -> Optional[MetadataResponse]:
    client_instance = OpenAlexClient(email=email)
    async with httpx.AsyncClient() as client:
        return await client_instance.get_by_doi(doi, client)
