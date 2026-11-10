import json
import re
import time
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.services.metadata_service import MetadataService
from app.clients.ollama_client import generate_text
from app.models.ollama_model import OllamaGenerateRequest
from app.services.ocde_service import get_ocde_areas_formatted
from app.services.ods_service import get_ods_areas_formatted
from app.models.classification_model import (
    OCDEClassificationResponse, 
    ODSClassificationResponse,
    OCDEClassificationItem,
    ODSClassificationItem,
    OCDEClassificationResult,
    ODSClassificationResult
)
from app.models.metadata_model import MetadataResponse
from app.models.db_models import (
    LLMClassificationLog, Category, ItemCategory
)

MODEL_EXACT_VERSION = "llama3.2:3b-instruct-q4_K_M"
PROMPT_VERSION = "v3.0"
PRODUCTION_TEMPERATURE = 0.0


class ClassificationService:
    """
    Microservicio 2: Clasificación Área OCDE / ODS (MS2).
    Inferencia semántica local con LLM Llama 3.2 (3B) en Ollama.
    Escribe exclusivamente en LLM_Classification_Log y Category.
    """

    def __init__(self):
        self.metadata_service = MetadataService()

    async def classify_item_for_enrichment(
        self,
        item_id: Any,
        title: Optional[str],
        abstract: Optional[str],
        keywords: Optional[str],
        db: Session,
        temperature: float = PRODUCTION_TEMPERATURE,
        repetition_number: int = 1
    ) -> Dict[str, Any]:
        """
        Ejecuta la clasificación combinada OCDE y ODS para un ItemEnrichment,
        registrando la bitácora inmutable en LLMClassificationLog (MS2).
        """
        ocde_res, ocde_log = await self.classify_ocde_with_logging(
            item_id=item_id,
            title=title,
            abstract=abstract,
            db=db,
            temperature=temperature,
            repetition_number=repetition_number
        )

        ods_res, ods_log = await self.classify_ods_with_logging(
            item_id=item_id,
            title=title,
            abstract=abstract,
            keywords=keywords,
            db=db,
            temperature=temperature,
            repetition_number=repetition_number
        )

        return {
            "ocde": ocde_res,
            "ods": ods_res,
            "ocde_log_id": ocde_log.id if ocde_log else None,
            "ods_log_id": ods_log.id if ods_log else None
        }

    async def classify_ocde_with_logging(
        self,
        item_id: Any,
        title: Optional[str],
        abstract: Optional[str],
        db: Session,
        temperature: float = PRODUCTION_TEMPERATURE,
        repetition_number: int = 1
    ) -> Tuple[OCDEClassificationResponse, Optional[LLMClassificationLog]]:
        """Inferencia OCDE con registro auditable en LLMClassificationLog."""
        start_time = time.time()
        areas_texto = get_ocde_areas_formatted()

        # Evaluación de suficiencia de texto (Sección 4.4)
        is_sufficient = bool(abstract and len(abstract.strip()) >= 50)

        prompt = f"""
Eres un bibliotecario académico experto. Tu tarea es analizar un artículo científico y seleccionar ÚNICAMENTE 1 o 2 disciplinas FORD OCDE (2007) que mejor definan la disciplina académica y metodológica del trabajo.

DATOS DEL ARTÍCULO:
- Título: {title or 'No disponible'}
- Resumen: {abstract or 'No disponible'}

LISTA DE DISCIPLINAS PERMITIDAS:
{areas_texto}

REGLAS ESTRICTAS:
1. SELECCIONA UN MÁXIMO DE 2 disciplinas de la lista anterior.
2. Si el título y resumen son insuficientes o ambiguos, asigna "is_info_sufficient": false.
3. Tu respuesta DEBE ser exclusivamente un JSON válido con la siguiente estructura:

{{
    "is_info_sufficient": true,
    "razonamiento_global": "Breve explicación de la selección metodológica",
    "clasificaciones": [
        {{
            "codigo_area": "ID Área",
            "nombre_area": "Nombre Área",
            "codigo_subarea": "ID Subárea",
            "nombre_subarea": "Nombre Subárea",
            "codigo_disciplina": "ID Disciplina (ej. 2.7)",
            "nombre_disciplina": "Nombre de la disciplina",
            "justificacion": "Justificación en español",
            "confidence_score": 0.95
        }}
    ]
}}
"""
        ollama_req = OllamaGenerateRequest(
            model=MODEL_EXACT_VERSION.split(":")[0],  # "llama3.2"
            prompt=prompt
        )

        log_entry = None
        clasificaciones = []
        razonamiento = None
        result_json = {}

        try:
            ollama_res = await generate_text(ollama_req)
            elapsed_ms = int((time.time() - start_time) * 1000)
            raw_text = ollama_res.response.strip()

            # Extracción robusta de JSON
            json_match = re.search(r'(\{.*\})', raw_text, re.DOTALL)
            if json_match:
                raw_text = json_match.group(1)

            result_json = json.loads(raw_text)
            is_sufficient = result_json.get("is_info_sufficient", is_sufficient)
            razonamiento = result_json.get("razonamiento_global", "")

            for item in result_json.get("clasificaciones", [])[:2]:
                clasificaciones.append(
                    OCDEClassificationItem(
                        codigo_area=str(item.get("codigo_area", "")),
                        nombre_area=str(item.get("nombre_area", "")),
                        codigo_subarea=str(item.get("codigo_subarea", "")),
                        nombre_subarea=str(item.get("nombre_subarea", "")),
                        codigo_disciplina=str(item.get("codigo_disciplina", "")),
                        nombre_disciplina=str(item.get("nombre_disciplina", "")),
                        justificacion=str(item.get("justificacion", "")),
                        confidence_score=float(item.get("confidence_score", 0.9))
                    )
                )

        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            is_sufficient = False
            razonamiento = f"Error en inferencia o parseo: {e}"
            result_json = {"error": str(e)}

        # Persistir en LLMClassificationLog (Dueño: MS2)
        if item_id:
            log_entry = LLMClassificationLog(
                id_item_enrichment=item_id,
                classification_type="OCDE",
                model_version=MODEL_EXACT_VERSION,
                prompt_template_version=PROMPT_VERSION,
                prompt=prompt[:2000],
                temperature=temperature,
                repetition_number=repetition_number,
                result_json=result_json,
                llm_reasoning=razonamiento,
                is_info_sufficient=is_sufficient,
                execution_time_ms=elapsed_ms,
                created_at=datetime.utcnow()
            )
            db.add(log_entry)
            db.commit()

        resp = OCDEClassificationResponse(
            clasificaciones=clasificaciones,
            is_info_sufficient=is_sufficient,
            razonamiento_global=razonamiento
        )
        return resp, log_entry

    async def classify_ods_with_logging(
        self,
        item_id: Any,
        title: Optional[str],
        abstract: Optional[str],
        keywords: Optional[str],
        db: Session,
        temperature: float = PRODUCTION_TEMPERATURE,
        repetition_number: int = 1
    ) -> Tuple[ODSClassificationResponse, Optional[LLMClassificationLog]]:
        """Inferencia ODS con registro auditable en LLMClassificationLog."""
        start_time = time.time()
        areas_texto = get_ods_areas_formatted()
        is_sufficient = bool(abstract and len(abstract.strip()) >= 50)

        prompt = f"""
Eres un experto en los 17 Objetivos de Desarrollo Sostenible (ODS) de la ONU (2015).
Tu tarea es clasificar el impacto o contribución socioeconómica/ambiental del siguiente artículo científico:

DATOS DEL ARTÍCULO:
- Título: {title or 'No disponible'}
- Resumen: {abstract or 'No disponible'}
- Palabras clave: {keywords or 'No disponible'}

LISTA DE ODS DISPONIBLES:
{areas_texto}

REGLAS ESTRICTAS:
1. SELECCIONA UN MÁXIMO DE 2 Objetivos de Desarrollo Sostenible representativos.
2. Si el texto es insuficiente para evaluar el impacto global, asigna "is_info_sufficient": false.
3. Responde exclusivamente con un JSON válido con la siguiente estructura:

{{
    "is_info_sufficient": true,
    "razonamiento_global": "Breve explicación de la contribución socioeconómica",
    "clasificaciones": [
        {{
            "numero_ods": "Número del ODS (ej. 3, 6, 13)",
            "nombre_ods": "Nombre del ODS",
            "justificacion": "Breve explicación de 2 oraciones en español",
            "confidence_score": 0.95
        }}
    ]
}}
"""
        ollama_req = OllamaGenerateRequest(
            model=MODEL_EXACT_VERSION.split(":")[0],
            prompt=prompt
        )

        log_entry = None
        clasificaciones = []
        razonamiento = None
        result_json = {}

        try:
            ollama_res = await generate_text(ollama_req)
            elapsed_ms = int((time.time() - start_time) * 1000)
            raw_text = ollama_res.response.strip()

            json_match = re.search(r'(\{.*\})', raw_text, re.DOTALL)
            if json_match:
                raw_text = json_match.group(1)

            result_json = json.loads(raw_text)
            is_sufficient = result_json.get("is_info_sufficient", is_sufficient)
            razonamiento = result_json.get("razonamiento_global", "")

            for item in result_json.get("clasificaciones", [])[:2]:
                clasificaciones.append(
                    ODSClassificationItem(
                        numero_ods=str(item.get("numero_ods", "")),
                        nombre_ods=str(item.get("nombre_ods", "")),
                        justificacion=str(item.get("justificacion", "")),
                        confidence_score=float(item.get("confidence_score", 0.9))
                    )
                )

        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            is_sufficient = False
            razonamiento = f"Error en inferencia o parseo ODS: {e}"
            result_json = {"error": str(e)}

        if item_id:
            log_entry = LLMClassificationLog(
                id_item_enrichment=item_id,
                classification_type="ODS",
                model_version=MODEL_EXACT_VERSION,
                prompt_template_version=PROMPT_VERSION,
                prompt=prompt[:2000],
                temperature=temperature,
                repetition_number=repetition_number,
                result_json=result_json,
                llm_reasoning=razonamiento,
                is_info_sufficient=is_sufficient,
                execution_time_ms=elapsed_ms,
                created_at=datetime.utcnow()
            )
            db.add(log_entry)
            db.commit()

        resp = ODSClassificationResponse(
            clasificaciones=clasificaciones,
            is_info_sufficient=is_sufficient,
            razonamiento_global=razonamiento
        )
        return resp, log_entry

    # Métodos legacy para compatibilidad con endpoints REST existentes
    async def classify_metadata_ocde(self, articulo: MetadataResponse) -> OCDEClassificationResponse:
        resp, _ = await self.classify_ocde_with_logging(
            item_id=None,
            title=articulo.title,
            abstract=articulo.abstract,
            db=None
        )
        resp.articulo = articulo
        return resp

    async def classify_metadata_ods(self, articulo: MetadataResponse) -> ODSClassificationResponse:
        resp, _ = await self.classify_ods_with_logging(
            item_id=None,
            title=articulo.title,
            abstract=articulo.abstract,
            keywords=", ".join(articulo.keywords) if articulo.keywords else None,
            db=None
        )
        resp.articulo = articulo
        return resp
