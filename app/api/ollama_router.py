from fastapi import APIRouter, Depends, HTTPException
from app.models.ollama_model import OllamaGenerateRequest, OllamaGenerateResponse
from app.services.ollama_service import OllamaService

router = APIRouter(
    prefix="/ollama",
    tags=["ollama"]
)

def get_ollama_service() -> OllamaService:
    return OllamaService()

@router.post("/generate", response_model=OllamaGenerateResponse)
async def generate(request: OllamaGenerateRequest, svc: OllamaService = Depends(get_ollama_service)):
    """
    Genera una respuesta de texto utilizando un modelo local en Ollama.
    """
    try:
        return await svc.generate_response(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
