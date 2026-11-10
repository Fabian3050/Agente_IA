from models.ollama_model import OllamaGenerateRequest, OllamaGenerateResponse
from services.ollama_client import generate_text, OllamaRequest

class OllamaService:
    async def generate_response(self, request: OllamaGenerateRequest) -> OllamaGenerateResponse:
        """
        Envía la solicitud de generación de texto a Ollama.
        """
        req = OllamaRequest(
            model=request.model,
            prompt=request.prompt,
            stream=request.stream
        )
        res = await generate_text(req)
        return OllamaGenerateResponse(
            model=request.model,
            response=res.response,
            done=res.done,
            total_duration=res.total_duration
        )

