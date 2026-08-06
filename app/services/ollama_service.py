from app.models.ollama_model import OllamaGenerateRequest, OllamaGenerateResponse
from app.clients.ollama_client import generate_text

class OllamaService:
    async def generate_response(self, request: OllamaGenerateRequest) -> OllamaGenerateResponse:
        """
        Envía la solicitud de generación de texto a Ollama.
        """
        # Aquí se podría añadir validación extra o lógica de negocio si es necesario.
        return await generate_text(request)
