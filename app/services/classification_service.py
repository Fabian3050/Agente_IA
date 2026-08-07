import json
from typing import Optional
from app.services.metadata_service import MetadataService
from app.clients.ollama_client import generate_text
from app.models.ollama_model import OllamaGenerateRequest
from app.services.ocde_service import get_ocde_areas_formatted
from app.models.classification_model import OCDEClassificationResponse

class ClassificationService:
    def __init__(self):
        self.metadata_service = MetadataService()

    async def classify_article_by_doi(self, doi: str, source: Optional[str] = None) -> OCDEClassificationResponse:
        # 1. Obtener metadatos desde las fuentes (CrossRef, OpenAlex, etc.)
        results = await self.metadata_service.get_metadata_by_doi(doi, source)
        if not results:
            raise Exception(f"No se encontraron metadatos para el DOI: {doi}")
            
        articulo = results[0] # Tomamos el primer resultado devuelto
        
        # 2. Cargar listado de áreas OCDE
        areas_texto = get_ocde_areas_formatted()
        
        # 3. Diseñar el Prompt para Llama 3.2
        prompt = f"""
Eres un experto en clasificación bibliométrica según el estándar OCDE (FORD/FOS).

Dado el siguiente artículo científico:
- Título: {articulo.title}
- Abstract: {articulo.abstract or 'No disponible'}

Clasifícalo en ÚNICAMENTE UNA de las siguientes Áreas OCDE disponibles:
{areas_texto}

Responde estrictamente en formato JSON válido con la siguiente estructura:
{{
  "codigo_ocde": "código elegido (ej. 6.1.B)",
  "area_ocde": "nombre exacto de la categoría elegida",
  "justificacion": "breve explicación en español de 2 oraciones del por qué corresponde a esa área"
}}
"""

        # 4. Consultar a Ollama
        ollama_req = OllamaGenerateRequest(
            model="llama3.2",
            prompt=prompt
        )
        
        ollama_res = await generate_text(ollama_req)
        
        # 5. Parsear la respuesta de Llama
        try:
            # Limpiamos bloques markdown ```json si el modelo los incluye
            raw_text = ollama_res.response.strip()
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0].strip()
                
            parsed = json.loads(raw_text)
            
            return OCDEClassificationResponse(
                codigo_ocde=parsed.get("codigo_ocde", "Desconocido"),
                area_ocde=parsed.get("area_ocde", "Desconocido"),
                justificacion=parsed.get("justificacion", ""),
                articulo=articulo
            )
        except Exception as e:
            # Fallback en caso de que el LLM no responda en JSON perfecto
            return OCDEClassificationResponse(
                codigo_ocde="Indeterminado",
                area_ocde=ollama_res.response,
                justificacion="Respuesta generada sin formato estricto JSON",
                articulo=articulo
            )
