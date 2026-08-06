from pydantic import BaseModel, Field
from typing import Optional

class OllamaGenerateRequest(BaseModel):
    model: str = Field(default="llama3", description="The name of the model to use")
    prompt: str = Field(..., description="The prompt to generate a response for")
    system: Optional[str] = Field(None, description="System message to (overrides what is defined in the Modelfile)")
    stream: bool = Field(False, description="If false the response will be returned as a single response object")

class OllamaGenerateResponse(BaseModel):
    model: str
    response: str
    done: bool
    total_duration: Optional[int] = None
