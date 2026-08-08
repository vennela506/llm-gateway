from app.models.schemas import ChatRequest, LLMResponse
from app.core.circuit_breaker import CircuitBreaker, OPEN
from app.providers.openai import OpenAIProvider
from app.providers.anthropic import AnthropicProvider
from app.providers.groq_provider import GroqProvider
from app.core.logger import logger


class FallbackRouter:
    def __init__(self):
        self.circuit_breaker = CircuitBreaker(failure_threshold=2, cooldown_seconds=30)

        # Instantiate our providers
        self.providers = {
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
            "groq": GroqProvider(),
        }

        # Define the fallback priority chain
        self.priority_chain = ["openai", "anthropic", "groq"]

    async def route_request(self, request: ChatRequest) -> LLMResponse:
        """
        Attempts to route the request through the priority chain.
        Respects circuit breaker states and falls back on failure.
        """
        errors = []

        for provider_name in self.priority_chain:
            # 1. Check Circuit Breaker Status
            state = await self.circuit_breaker.get_state(provider_name)

            if state == OPEN:
                logger.warning("circuit_open_skip", provider=provider_name)
                continue

            provider = self.providers[provider_name]

            # 2. Attempt the API Call
            try:
                logger.info("attempting_generation", provider=provider_name)
                response = await provider.generate(request)

                # 3. On success, tell the circuit breaker everything is healthy
                await self.circuit_breaker.record_success(provider_name)
                return response

            except Exception as e:
                # 4. On failure, record the error and trigger fallback
                logger.error("provider_failure", provider=provider_name, error=str(e))
                await self.circuit_breaker.record_failure(provider_name)
                errors.append(f"{provider_name}: {str(e)}")
                continue  # Try the next provider in the chain

        # If we exit the loop, ALL providers failed
        raise Exception(f"All providers failed. Errors: {errors}")
