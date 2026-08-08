from openai import AsyncOpenAI
from app.providers.base import BaseLLMProvider
from app.models.schemas import ChatRequest, LLMResponse
from app.core.config import settings


class OpenAIProvider(BaseLLMProvider):
    provider_name = "openai"

    def __init__(self):
        # Initialize the async client with our key from the settings
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def generate(self, request: ChatRequest) -> LLMResponse:
        # 1. Translate our standard request into OpenAI's format
        messages = [
            {"role": msg.role, "content": msg.content} for msg in request.messages
        ]

        # Default to a cheap model for testing if none is specified
        model = "gpt-3.5-turbo" if request.model == "default" else request.model

        # 2. Make the API call
        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )

        # 3. Translate OpenAI's response back into our standard LLMResponse
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
