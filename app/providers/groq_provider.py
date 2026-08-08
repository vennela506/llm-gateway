from groq import AsyncGroq
from app.providers.base import BaseLLMProvider
from app.models.schemas import ChatRequest, LLMResponse
from app.core.config import settings


class GroqProvider(BaseLLMProvider):
    provider_name = "groq"

    def __init__(self):
        # Initialize the async client with our key from settings
        self.client = AsyncGroq(api_key=settings.groq_api_key)

    async def generate(self, request: ChatRequest) -> LLMResponse:
        messages = [
            {"role": msg.role, "content": msg.content} for msg in request.messages
        ]

        # Default to a blazing fast, free open-source model on Groq
        model = "llama-3.1-8b-instant" if request.model == "default" else request.model

        # The API call structure is identical to OpenAI's
        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )

        usage = response.usage
        return LLMResponse(
            id=response.id,
            content=response.choices[0].message.content or "",
            provider=self.provider_name,
            model=response.model,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
        )
