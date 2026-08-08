from anthropic import AsyncAnthropic
from app.providers.base import BaseLLMProvider
from app.models.schemas import ChatRequest, LLMResponse
from app.core.config import settings


class AnthropicProvider(BaseLLMProvider):
    provider_name = "anthropic"

    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def generate(self, request: ChatRequest) -> LLMResponse:
        system_prompt = ""
        anthropic_messages = []

        # 1. Translate: Extract system prompts (Anthropic requires them separately)
        for msg in request.messages:
            if msg.role == "system":
                system_prompt += msg.content + "\n"
            else:
                anthropic_messages.append({"role": msg.role, "content": msg.content})

        model = (
            "claude-3-haiku-20240307" if request.model == "default" else request.model
        )

        # 2. Build kwargs for the API call
        kwargs = {
            "model": model,
            "max_tokens": request.max_tokens or 1000,
            "temperature": request.temperature,
            "messages": anthropic_messages,
        }
        if system_prompt:
            kwargs["system"] = system_prompt.strip()

        # 3. Make the API call
        response = await self.client.messages.create(**kwargs)

        # 4. Translate back to our standard response schema
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens

        return LLMResponse(
            id=response.id,
            content=response.content[0].text,
            provider=self.provider_name,
            model=response.model,
            prompt_tokens=input_tokens,
            completion_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
        )
