import httpx
import os
from typing import Optional
from app.models.ollama_model import OllamaGenerateRequest, OllamaGenerateResponse

# Permite configurar la URL de Ollama mediante variables de entorno, o usa el default local (127.0.0.1 evita problemas IPv6 en Windows)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")

async def generate_text(request: OllamaGenerateRequest) -> OllamaGenerateResponse:
    url = f"{OLLAMA_BASE_URL}/api/generate"
    
    payload = request.model_dump(exclude_none=True)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, timeout=120.0)
            response.raise_for_status()
            data = response.json()
            
            return OllamaGenerateResponse(
                model=data.get("model", request.model),
                response=data.get("response", ""),
                done=data.get("done", True),
                total_duration=data.get("total_duration")
            )
        except httpx.HTTPStatusError as e:
            print(f"Ollama HTTP error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to communicate with Ollama: {e.response.text}")
        except Exception as e:
            error_msg = str(e) or repr(e)
            print(f"Error connecting to Ollama at {url}: {error_msg}")
            raise Exception(f"Failed to connect to Ollama: {error_msg}")
