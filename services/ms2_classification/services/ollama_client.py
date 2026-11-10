import os
import httpx
from pydantic import BaseModel
from typing import Optional, Dict, Any

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


class OllamaRequest(BaseModel):
    model: str = "llama3.2"
    prompt: str
    stream: bool = False
    options: Optional[Dict[str, Any]] = None


class OllamaResponse(BaseModel):
    response: str
    done: bool = True
    total_duration: Optional[int] = None


async def generate_text(req: OllamaRequest) -> OllamaResponse:
    url = f"{OLLAMA_BASE_URL.rstrip('/')}/api/generate"
    payload = {
        "model": req.model,
        "prompt": req.prompt,
        "stream": False,
        "options": req.options or {"temperature": 0.0}
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return OllamaResponse(
                response=data.get("response", ""),
                done=data.get("done", True),
                total_duration=data.get("total_duration")
            )
        except Exception as e:
            print(f"[MS2 Ollama] Error conectando con {url}: {e}")
            raise Exception(f"Falla en inferencia Ollama: {e}")

