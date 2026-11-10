import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from models import CandidateMatch, ExternalAPISource, RetrievalResponse, CandidateMetadataDTO
from clients.crossref_client import get_by_doi_crossref, search_crossref
from clients.openalex_client import OpenAlexClient, get_by_doi_openalex
from clients.unpaywall_client import get_metadata_by_doi_unpaywall
from clients.europe_pmc_client import get_by_doi_europe_pmc, search_europe_pmc
from clients.semantic_scholar_client import get_by_doi_semantic_scholar, search_semantic_scholar
from services.matching_service import calculate_similarity, evaluate_doi_match, evaluate_no_doi_match


class MS1RetrievalWorker:
    """
    Lógica de recuperación y validación para MS1.
    Escribe exclusivamente en Candidate_Match y External_API_Source.
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

    async def execute_retrieval(
        self,
        item_id: uuid.UUID,
        doi: Optional[str],
        title: Optional[str],
        db: Session
    ) -> Dict[str, Any]:
        results_by_source = {}
        query_statuses = {}
        match_scores = {}

        has_doi = bool(doi and doi.strip())
        doi_clean = doi.strip() if has_doi else None

        sources = ["Crossref", "OpenAlex", "Unpaywall", "Semantic Scholar", "Europe PMC"]

        for source_name in sources:
            source_id = self._get_external_source_id(db, source_name)
            meta = None
            query_result = "sin_datos"
            score = 0.0
            candidate_doi = doi_clean

            try:
                if has_doi:
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
                    if title:
                        if source_name == "Crossref":
                            res_list = await search_crossref(title, limit=1)
                            meta = res_list[0] if res_list else None
                        elif source_name == "OpenAlex":
                            candidates = await self.openalex_client.search_candidates_by_title(title, limit=1)
                            if candidates:
                                meta = candidates[0].get("metadata")
                                candidate_doi = meta.doi if meta else None
                        elif source_name == "Semantic Scholar":
                            res_list = await search_semantic_scholar(title, limit=1)
                            meta = res_list[0] if res_list else None
                        elif source_name == "Europe PMC":
                            res_list = await search_europe_pmc(title, limit=1)
                            meta = res_list[0] if res_list else None

                if meta:
                    query_result = "exitosa"
                    candidate_doi = meta.doi or candidate_doi
                    score = calculate_similarity(title, meta.title)
                else:
                    query_result = "sin_datos"

            except Exception as e:
                query_result = "fallida"
                print(f"[MS1] Error consultando {source_name}: {e}")

            raw_json = meta.model_dump() if meta else {"error": query_result}
            cm = CandidateMatch(
                id_item_enrichment=item_id,
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

        # Evaluación de umbrales
        max_score = 0.0
        best_source = None
        for s_name, score in match_scores.items():
            if score > max_score and results_by_source.get(s_name):
                max_score = score
                best_source = s_name

        if has_doi:
            if max_score > 0.0 and max_score < 0.85:
                outcome = "COINCIDENCIA_DUDOSA"
            elif max_score >= 0.85:
                outcome = "ALTA_COINCIDENCIA"
            else:
                outcome = "SIN_DATOS"
        else:
            if max_score >= 0.95:
                outcome = "ALTA_COINCIDENCIA"
            elif max_score >= 0.70:
                outcome = "COINCIDENCIA_DUDOSA"
            else:
                outcome = "DESCARTADA"

        consolidated = self._consolidate(results_by_source, doi_clean)

        return {
            "outcome": outcome,
            "max_score": max_score,
            "best_source": best_source,
            "consolidated": consolidated,
            "query_statuses": query_statuses
        }

    def _consolidate(self, results_by_source: Dict[str, Any], best_doi: Optional[str]) -> Dict[str, Any]:
        abstract = None
        abstract_source = None
        for s in ["Crossref", "OpenAlex", "Semantic Scholar", "Europe PMC"]:
            meta = results_by_source.get(s)
            if meta and meta.abstract and len(meta.abstract.strip()) > 20:
                abstract = meta.abstract.strip()
                abstract_source = s
                break

        author_kws = set()
        for s, meta in results_by_source.items():
            if meta:
                kws = getattr(meta, "author_keywords", None) or getattr(meta, "keywords", None) or []
                for k in kws:
                    if k and len(k.strip()) > 2:
                        author_kws.add(k.strip())

        automated_concepts = set()
        openalex_meta = results_by_source.get("OpenAlex")
        if openalex_meta and getattr(openalex_meta, "automated_concepts", None):
            for c in openalex_meta.automated_concepts:
                if c:
                    automated_concepts.add(c.strip())

        funding_agency = None
        funding_id = None
        funding_grant = None
        for s in ["Crossref", "OpenAlex", "Europe PMC"]:
            meta = results_by_source.get(s)
            if meta and (getattr(meta, "funding_agency", None) or getattr(meta, "funding_grant_number", None)):
                funding_agency = getattr(meta, "funding_agency", None)
                funding_id = getattr(meta, "funding_id", None)
                funding_grant = getattr(meta, "funding_grant_number", None)
                break

        oa_status = None
        license_val = None
        version_type = None
        for s in ["Unpaywall", "OpenAlex", "Crossref"]:
            meta = results_by_source.get(s)
            if meta and (getattr(meta, "oa_status", None) or getattr(meta, "license", None)):
                oa_status = oa_status or getattr(meta, "oa_status", None)
                license_val = license_val or getattr(meta, "license", None)
                version_type = version_type or getattr(meta, "version_type", None)

        final_doi = best_doi
        if not final_doi:
            for s, meta in results_by_source.items():
                if meta and getattr(meta, "doi", None):
                    final_doi = meta.doi
                    break

        return {
            "doi": final_doi,
            "abstract": abstract,
            "abstract_source": abstract_source,
            "author_keywords": ", ".join(sorted(author_kws)) if author_kws else None,
            "automated_concepts": ", ".join(sorted(automated_concepts)) if automated_concepts else None,
            "funding_agency": funding_agency,
            "funding_id": funding_id,
            "funding_grant_number": funding_grant,
            "oa_status": oa_status,
            "license": license_val,
            "version_type": version_type
        }

