import json
from typing import Optional
from app.services.metadata_service import MetadataService
from app.clients.ollama_client import generate_text
from app.models.ollama_model import OllamaGenerateRequest
from app.services.ocde_service import get_ocde_areas_formatted
from app.services.ods_service import get_ods_areas_formatted
from app.models.classification_model import (
    OCDEClassificationResponse, 
    ODSClassificationResponse,
    OCDEClassificationItem,
    ODSClassificationItem
)

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

Clasifícalo en UNA O MÁS (si aplican varias) de las siguientes Áreas OCDE disponibles:
{areas_texto}

Responde estrictamente en formato JSON válido con la siguiente estructura (como una lista bajo la clave "clasificaciones"):
{{
  "clasificaciones": [
    {{
      "codigo_ocde": "código elegido (ej. 6.1.B)",
      "area_ocde": "nombre exacto de la categoría elegida",
      "justificacion": "breve explicación en español de 2 oraciones del por qué corresponde a esa área"
    }}
  ]
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
            
            clasificaciones_data = parsed.get("clasificaciones", [])
            clasificaciones = []
            for item in clasificaciones_data:
                clasificaciones.append(
                    OCDEClassificationItem(
                        codigo_ocde=item.get("codigo_ocde", "Desconocido"),
                        area_ocde=item.get("area_ocde", "Desconocido"),
                        justificacion=item.get("justificacion", "")
                    )
                )
            
            return OCDEClassificationResponse(
                clasificaciones=clasificaciones,
                articulo=articulo
            )
        except Exception as e:
            # Fallback en caso de que el LLM no responda en JSON perfecto
            return OCDEClassificationResponse(
                clasificaciones=[
                    OCDEClassificationItem(
                        codigo_ocde="Indeterminado",
                        area_ocde="Indeterminado",
                        justificacion="Respuesta generada sin formato estricto JSON: " + str(ollama_res.response)
                    )
                ],
                articulo=articulo
            )

    async def classify_article_by_ods(self, doi: str, source: Optional[str] = None) -> ODSClassificationResponse:
        # 1. Obtener metadatos desde las fuentes (CrossRef, OpenAlex, etc.)
        results = await self.metadata_service.get_metadata_by_doi(doi, source)
        if not results:
            raise Exception(f"No se encontraron metadatos para el DOI: {doi}")
            
        articulo = results[0] # Tomamos el primer resultado devuelto
        keywords_text = ", ".join(articulo.keywords) if articulo.keywords else "No disponibles"
        
        # 2. Cargar listado de áreas ODS
        areas_texto = get_ods_areas_formatted()
        
        # 3. Diseñar el Prompt para Llama 3.2
        prompt = f"""
                    Eres un experto en Objetivos de Desarrollo Sostenible (ODS) de las Naciones Unidas.                    
                    Dado el siguiente artículo científico:                   
                    - Título: {articulo.title}
                    - Abstract: {articulo.abstract or 'No disponible'}
                    - Palabras clave: {keywords_text}

                    Clasifícalo en UNA O MÁS (si aplican varias) de los siguientes ODS disponibles que sea el más representativo y adecuado:
                    {areas_texto}

                    Responde estrictamente en formato JSON válido con la siguiente estructura (como una lista bajo la clave "clasificaciones"):
                    {{
                      "clasificaciones": [
                        {{
                          "numero_ods": "número o código del ODS elegido (ej. 1, 2, 3...)",
                          "nombre_ods": "nombre exacto de la categoría ODS elegida",
                          "justificacion": "breve explicación en español de 2 oraciones del por qué el título, resumen o palabras clave corresponden a este ODS"
                        }}
                      ]
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
            
            clasificaciones_data = parsed.get("clasificaciones", [])
            clasificaciones = []
            for item in clasificaciones_data:
                clasificaciones.append(
                    ODSClassificationItem(
                        numero_ods=str(item.get("numero_ods", "Desconocido")),
                        nombre_ods=item.get("nombre_ods", "Desconocido"),
                        justificacion=item.get("justificacion", "")
                    )
                )
            
            return ODSClassificationResponse(
                clasificaciones=clasificaciones,
                articulo=articulo
            )
        except Exception as e:
            # Fallback en caso de que el LLM no responda en JSON perfecto
            return ODSClassificationResponse(
                clasificaciones=[
                    ODSClassificationItem(
                        numero_ods="Indeterminado",
                        nombre_ods="Indeterminado",
                        justificacion="Respuesta generada sin formato estricto JSON: " + str(ollama_res.response)
                    )
                ],
                articulo=articulo
            )
