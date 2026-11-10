import json
import re
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from models import LLMClassificationLog, Category, OCDEItemDTO, ODSItemDTO, ClassificationResultResponse
from services.ollama_client import generate_text, OllamaRequest
from services.ocde_service import get_ocde_areas_formatted
from services.ods_service import get_ods_areas_formatted

MODEL_VERSION = "llama3.2:3b-instruct-q4_K_M"
PROMPT_VERSION = "v3.0"


class MS2ClassificationWorker:
    """
    Microservicio 2: Inferencia semántica con LLM local (Ollama).
    Escribe exclusivamente en LLM_Classification_Log y gestiona Category.
    """

    async def execute_classification(
        self,
        item_id: uuid.UUID,
        title: Optional[str],
        abstract: Optional[str],
        keywords: Optional[str],
        db: Session,
        temperature: float = 0.0,
        repetition_number: int = 1
    ) -> ClassificationResultResponse:
        start_total = time.time()

        ocde_items, ocde_suff, ocde_reason, ocde_ms = await self._classify_ocde(
            item_id=item_id,
            title=title,
            abstract=abstract,
            db=db,
            temperature=temperature,
            repetition_number=repetition_number
        )

        ods_items, ods_suff, ods_reason, ods_ms = await self._classify_ods(
            item_id=item_id,
            title=title,
            abstract=abstract,
            keywords=keywords,
            db=db,
            temperature=temperature,
            repetition_number=repetition_number
        )

        total_ms = int((time.time() - start_total) * 1000)
        overall_suff = ocde_suff and ods_suff

        return ClassificationResultResponse(
            is_info_sufficient=overall_suff,
            ocde_categories=ocde_items,
            ods_categories=ods_items,
            ocde_reasoning=ocde_reason,
            ods_reasoning=ods_reason,
            execution_time_total_ms=total_ms
        )

    async def _classify_ocde(
        self,
        item_id: uuid.UUID,
        title: Optional[str],
        abstract: Optional[str],
        db: Session,
        temperature: float,
        repetition_number: int
    ) -> Tuple[List[OCDEItemDTO], bool, str, int]:
        t0 = time.time()
        areas_text = get_ocde_areas_formatted()
        is_suff = bool(abstract and len(abstract.strip()) >= 50)

        prompt = f"""
Eres un bibliotecario académico experto. Selecciona ÚNICAMENTE 1 o 2 disciplinas FORD OCDE (2007) para este artículo:
TÍTULO: {title or 'No disponible'}
RESUMEN: {abstract or 'No disponible'}

LISTA PERMITIDA:
{areas_text}

REGLAS:
1. Máximo 2 disciplinas.
2. Si la información es insuficiente, pon is_info_sufficient: false.
3. Responde SOLO un JSON:
{{
  "is_info_sufficient": true,
  "razonamiento": "explicación",
  "clasificaciones": [
    {{
      "codigo_area": "ID",
      "nombre_area": "Nombre",
      "codigo_disciplina": "ID",
      "nombre_disciplina": "Nombre",
      "justificacion": "texto",
      "confidence_score": 0.95
    }}
  ]
}}
"""
        items = []
        reason = ""
        res_json = {}

        try:
            res = await generate_text(OllamaRequest(
                model=MODEL_VERSION.split(":")[0],
                prompt=prompt,
                options={"temperature": temperature}
            ))
            raw = res.response.strip()
            m = re.search(r'(\{.*\})', raw, re.DOTALL)
            if m: raw = m.group(1)
            res_json = json.loads(raw)

            is_suff = res_json.get("is_info_sufficient", is_suff)
            reason = res_json.get("razonamiento", "")
            for it in res_json.get("clasificaciones", [])[:2]:
                items.append(OCDEItemDTO(
                    codigo_area=str(it.get("codigo_area", "")),
                    nombre_area=str(it.get("nombre_area", "")),
                    codigo_subarea=str(it.get("codigo_subarea", "")),
                    nombre_subarea=str(it.get("nombre_subarea", "")),
                    codigo_disciplina=str(it.get("codigo_disciplina", "")),
                    nombre_disciplina=str(it.get("nombre_disciplina", "")),
                    justificacion=str(it.get("justificacion", "")),
                    confidence_score=float(it.get("confidence_score", 0.95))
                ))
        except Exception as e:
            reason = f"Error en inferencia OCDE: {e}"
            res_json = {"error": str(e)}

        elapsed = int((time.time() - t0) * 1000)

        # Guardar bitácora MS2
        log = LLMClassificationLog(
            id_item_enrichment=item_id,
            classification_type="OCDE",
            model_version=MODEL_VERSION,
            prompt_template_version=PROMPT_VERSION,
            prompt=prompt[:2000],
            temperature=temperature,
            repetition_number=repetition_number,
            result_json=res_json,
            llm_reasoning=reason,
            is_info_sufficient=is_suff,
            execution_time_ms=elapsed,
            created_at=datetime.utcnow()
        )
        db.add(log)
        db.commit()

        return items, is_suff, reason, elapsed

    async def _classify_ods(
        self,
        item_id: uuid.UUID,
        title: Optional[str],
        abstract: Optional[str],
        keywords: Optional[str],
        db: Session,
        temperature: float,
        repetition_number: int
    ) -> Tuple[List[ODSItemDTO], bool, str, int]:
        t0 = time.time()
        areas_text = get_ods_areas_formatted()
        is_suff = bool(abstract and len(abstract.strip()) >= 50)

        prompt = f"""
Eres un experto en los 17 ODS de la ONU (2015). Clasifica el impacto socioeconómico de este artículo en máximo 2 ODS:
TÍTULO: {title or 'No disponible'}
RESUMEN: {abstract or 'No disponible'}
PALABRAS CLAVE: {keywords or 'No disponible'}

LISTA ODS:
{areas_text}

REGLAS:
1. Máximo 2 ODS.
2. Si la información es insuficiente, is_info_sufficient: false.
3. Responde SOLO un JSON:
{{
  "is_info_sufficient": true,
  "razonamiento": "explicación",
  "clasificaciones": [
    {{
      "numero_ods": "3",
      "nombre_ods": "Salud y Bienestar",
      "justificacion": "explicación",
      "confidence_score": 0.95
    }}
  ]
}}
"""
        items = []
        reason = ""
        res_json = {}

        try:
            res = await generate_text(OllamaRequest(
                model=MODEL_VERSION.split(":")[0],
                prompt=prompt,
                options={"temperature": temperature}
            ))
            raw = res.response.strip()
            m = re.search(r'(\{.*\})', raw, re.DOTALL)
            if m: raw = m.group(1)
            res_json = json.loads(raw)

            is_suff = res_json.get("is_info_sufficient", is_suff)
            reason = res_json.get("razonamiento", "")
            for it in res_json.get("clasificaciones", [])[:2]:
                items.append(ODSItemDTO(
                    numero_ods=str(it.get("numero_ods", "")),
                    nombre_ods=str(it.get("nombre_ods", "")),
                    justificacion=str(it.get("justificacion", "")),
                    confidence_score=float(it.get("confidence_score", 0.95))
                ))
        except Exception as e:
            reason = f"Error en inferencia ODS: {e}"
            res_json = {"error": str(e)}

        elapsed = int((time.time() - t0) * 1000)

        log = LLMClassificationLog(
            id_item_enrichment=item_id,
            classification_type="ODS",
            model_version=MODEL_VERSION,
            prompt_template_version=PROMPT_VERSION,
            prompt=prompt[:2000],
            temperature=temperature,
            repetition_number=repetition_number,
            result_json=res_json,
            llm_reasoning=reason,
            is_info_sufficient=is_suff,
            execution_time_ms=elapsed,
            created_at=datetime.utcnow()
        )
        db.add(log)
        db.commit()

        return items, is_suff, reason, elapsed

