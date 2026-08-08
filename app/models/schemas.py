from pydantic import BaseModel, Field
from typing import List, Optional

# --- Requests ---


class Message(BaseModel):
    role: str = Field(..., description="Role of the sender (system, user, assistant)")
    content: str = Field(..., description="The content of the message")


class ChatRequest(BaseModel):
    messages: List[Message]
    model: Optional[str] = Field("default", description="The model to use")
    max_tokens: Optional[int] = Field(1000, description="Max tokens to generate")
    temperature: Optional[float] = Field(0.7, description="Randomness of the response")


# --- Responses ---


class LLMResponse(BaseModel):
    id: str
    content: str
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
