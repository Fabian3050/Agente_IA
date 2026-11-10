import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.db_models import (
    CandidateMatch, ExternalAPISource, ItemEnrichment, Status, ProposalStatus
)
from app.models.metadata_model import MetadataResponse
from app.clients.crossref_client import get_by_doi_crossref, search_crossref
from app.clients.openalex_client import OpenAlexClient, get_by_doi_openalex
from app.clients.unpaywall_client import get_metadata_by_doi_unpaywall
from app.clients.europe_pmc_client import get_by_doi_europe_pmc, search_europe_pmc
from app.clients.semantic_scholar_client import get_by_doi_semantic_scholar, search_semantic_scholar
from app.services.matching_service import (
    evaluate_doi_match, evaluate_no_doi_match, calculate_similarity
)


class MetadataRetrievalServiceMS1:
    """
    Microservicio 1: Recuperación y Validación de Metadatos (MS1).
    Consulta asíncrona a APIs científicas (Crossref, OpenAlex, Unpaywall, Europe PMC, Semantic Scholar).
    Aplica fuzzy matching, umbrales de certidumbre y escribe exclusivamente en CandidateMatch y ExternalAPISource.
    """

    def __init__(self):
        self.openalex_client = OpenAlexClient()

    def _get_external_source_id(self, db: Session, source_name: str) -> int:
        src = db.query(ExternalAPISource).filter(ExternalAPISource.name == source_name).first()
        if not src:
            src = ExternalAPISource(name=source_name, base_url="", is_active=True)
            db.add(src)
            db.commit()
            db.refresh(src)
        return src.id

    async def retrieve_for_item(
        self,
        item: ItemEnrichment,
        db: Session,
        dspace_author: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta el protocolo completo de recuperación de metadatos para un ítem según la Sección 3.
        Devuelve el estado resultante ('ALTA_COINCIDENCIA', 'COINCIDENCIA_DUDOSA', 'SIN_DATOS', 'FALLA')
        y los metadatos consolidados.
        """
        results_by_source: Dict[str, Optional[MetadataResponse]] = {}
        raw_responses: Dict[str, Any] = {}
        query_statuses: Dict[str, str] = {}
        match_scores: Dict[str, float] = {}

        has_doi = bool(item.doi and item.doi.strip())
        doi_clean = item.doi.strip() if has_doi else None

        # ---------------------------------------------------------------------
        # 1. CONSULTAS A FUENTES EXTERNAS
        # ---------------------------------------------------------------------
        # Fuentes a consultar: Crossref, OpenAlex, Unpaywall, Semantic Scholar, Europe PMC
        sources = ["Crossref", "OpenAlex", "Unpaywall", "Semantic Scholar", "Europe PMC"]

        for source_name in sources:
            source_id = self._get_external_source_id(db, source_name)
            meta: Optional[MetadataResponse] = None
            query_result = "sin_datos"
            score: float = 0.0
            candidate_doi = doi_clean

            try:
                if has_doi:
                    # Búsqueda directa por DOI
                    if source_name == "Crossref":
                        meta = await get_by_doi_crossref(doi_clean)
                    elif source_name == "OpenAlex":
                        meta = await get_by_doi_openalex(doi_clean)
                    elif source_name == "Unpaywall":
                        meta = await get_metadata_by_doi_unpaywall(doi_clean)
                    elif source_name == "Semantic Scholar":
                        meta = await get_by_doi_semantic_scholar(doi_clean)
                    elif source_name == "Europe PMC":
                        meta = await get_by_doi_europe_pmc(doi_clean)
                else:
                    # Búsqueda sin DOI por título normalizado
                    if item.title:
                        if source_name == "Crossref":
                            res_list = await search_crossref(item.title, limit=1)
                            meta = res_list[0] if res_list else None
                        elif source_name == "OpenAlex":
                            candidates = await self.openalex_client.search_candidates_by_title(item.title, limit=1)
                            if candidates:
                                meta = candidates[0].get("metadata")
                                candidate_doi = meta.doi if meta else None
                        elif source_name == "Semantic Scholar":
                            res_list = await search_semantic_scholar(item.title, limit=1)
                            meta = res_list[0] if res_list else None
                        elif source_name == "Europe PMC":
                            res_list = await search_europe_pmc(item.title, limit=1)
                            meta = res_list[0] if res_list else None

                if meta:
                    query_result = "exitosa"
                    candidate_doi = meta.doi or candidate_doi
                    # Evaluar similitud textual de título
                    score = calculate_similarity(item.title, meta.title)
                else:
                    query_result = "sin_datos"

            except Exception as e:
                query_result = "fallida"
                print(f"[MS1] Falla consultando {source_name} para ítem {item.uuid_dspace}: {e}")

            # Registrar estrictamente en CandidateMatch (Dueño: MS1)
            raw_json = meta.model_dump() if meta else {"error": query_result}
            cm = CandidateMatch(
                id_item_enrichment=item.id,
                id_external_source=source_id,
                candidate_doi=candidate_doi,
                match_score=score,
                query_result=query_result,
                raw_metadata_json=raw_json,
                retrieved_at=datetime.utcnow()
            )
            db.add(cm)

            results_by_source[source_name] = meta
            query_statuses[source_name] = query_result
            match_scores[source_name] = score

        db.commit()

        # ---------------------------------------------------------------------
        # 2. EVALUACIÓN DE FUZZY MATCHING SEGÚN PROTOCOLO (Sección 3.2)
        # ---------------------------------------------------------------------
        # Verificar si hay coincidencia válida o dudosa
        best_source = None
        max_score = 0.0
        for s_name, score in match_scores.items():
            if score > max_score and results_by_source.get(s_name):
                max_score = score
                best_source = s_name

        if has_doi:
            # Si tiene DOI: validar que el título retornado no difiera sintácticamente (< 85%)
            if max_score > 0.0 and max_score < 0.85:
                # Similitud menor a 85% con DOI registrado -> Coincidencia dudosa
                match_outcome = "COINCIDENCIA_DUDOSA"
            elif max_score >= 0.85:
                match_outcome = "ALTA_COINCIDENCIA"
            else:
                match_outcome = "SIN_DATOS"
        else:
            # Sin DOI: calibración de umbrales
            if max_score >= 0.95:
                match_outcome = "ALTA_COINCIDENCIA"
            elif max_score >= 0.70:
                match_outcome = "COINCIDENCIA_DUDOSA"
            else:
                match_outcome = "DESCARTADA"

        # ---------------------------------------------------------------------
        # 3. CONSOLIDACIÓN DE METADATOS SEGÚN REGLAS DE LIMPIEZA (Sección 3.4)
        # ---------------------------------------------------------------------
        consolidated = self._consolidate_metadata(results_by_source, best_doi=doi_clean)

        return {
            "outcome": match_outcome,
            "max_score": max_score,
            "best_source": best_source,
            "consolidated": consolidated,
            "results_by_source": results_by_source,
            "query_statuses": query_statuses
        }

    def _consolidate_metadata(
        self,
        results_by_source: Dict[str, Optional[MetadataResponse]],
        best_doi: Optional[str]
    ) -> Dict[str, Any]:
        """
        Aplica las reglas especializadas de la Sección 3.4:
        - Abstract: orden de confiabilidad Crossref > OpenAlex > Semantic Scholar > Europe PMC
        - dc.subject: palabras clave de autor explícitas
        - cris.concept: conceptos automáticos algorítmicos
        - Financiamiento desglosado: funding_agency, funding_id, funding_grant_number
        - Derechos de acceso: Gold, Green, Bronze, Hybrid, Closed
        - Versión de manuscrito: Preprint, Postprint, PublishedVersion
        """
        # Prioridad de Abstract: Crossref > OpenAlex > Semantic Scholar > Europe PMC
        abstract = None
        abstract_source = None
        for s in ["Crossref", "OpenAlex", "Semantic Scholar", "Europe PMC"]:
            meta = results_by_source.get(s)
            if meta and meta.abstract and len(meta.abstract.strip()) > 20:
                abstract = meta.abstract.strip()
                abstract_source = s
                break

        # Palabras clave del autor (dc.subject)
        author_keywords_set = set()
        for s, meta in results_by_source.items():
            if meta:
                kws = meta.author_keywords or meta.keywords or []
                for kw in kws:
                    if kw and len(kw.strip()) > 2:
                        author_keywords_set.add(kw.strip())

        # Conceptos automáticos algorítmicos (cris.concept)
        automated_concepts_set = set()
        openalex_meta = results_by_source.get("OpenAlex")
        if openalex_meta and openalex_meta.automated_concepts:
            for c in openalex_meta.automated_concepts:
                if c:
                    automated_concepts_set.add(c.strip())

        # Financiamiento desglosado (priorizar Crossref u OpenAlex)
        funding_agency = None
        funding_id = None
        funding_grant = None
        for s in ["Crossref", "OpenAlex", "Europe PMC"]:
            meta = results_by_source.get(s)
            if meta and (meta.funding_agency or meta.funding_id or meta.funding_grant_number):
                funding_agency = meta.funding_agency
                funding_id = meta.funding_id
                funding_grant = meta.funding_grant_number
                break

        # Acceso abierto, Licencia y Versión (priorizar Unpaywall u OpenAlex)
        oa_status = None
        license_val = None
        version_type = None
        for s in ["Unpaywall", "OpenAlex", "Crossref"]:
            meta = results_by_source.get(s)
            if meta and (meta.oa_status or meta.license or meta.version_type):
                oa_status = oa_status or meta.oa_status
                license_val = license_val or meta.license
                version_type = version_type or meta.version_type

        # Si aún no hay DOI pero OpenAlex o Crossref encontraron uno
        final_doi = best_doi
        if not final_doi:
            for s, meta in results_by_source.items():
                if meta and meta.doi:
                    final_doi = meta.doi
                    break

        return {
            "doi": final_doi,
            "abstract": abstract,
            "abstract_source": abstract_source,
            "author_keywords": ", ".join(sorted(author_keywords_set)) if author_keywords_set else None,
            "automated_concepts": ", ".join(sorted(automated_concepts_set)) if automated_concepts_set else None,
            "funding_agency": funding_agency,
            "funding_id": funding_id,
            "funding_grant_number": funding_grant,
            "oa_status": oa_status,
            "license": license_val,
            "version_type": version_type
        }

