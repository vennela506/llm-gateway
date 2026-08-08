from app.core.redis import redis_client

# Circuit Breaker States
CLOSED = "CLOSED"  # Normal operation, API is healthy
OPEN = "OPEN"  # API is failing, block requests
HALF_OPEN = "HALF_OPEN"  # Cooldown finished, testing if API is back online


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, cooldown_seconds: int = 60):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds

    async def get_state(self, provider_name: str) -> str:
        """Determines the current state of the provider."""
        state_key = f"cb:state:{provider_name}"
        cooldown_key = f"cb:cooldown:{provider_name}"

        state = await redis_client.get(state_key)
        # redis_client.get may return bytes; ensure we return a str
        if isinstance(state, (bytes, bytearray)):
            state = state.decode()
        state = state or CLOSED

        # If it's OPEN, check if the cooldown has expired
        if state == OPEN:
            cooldown_active = await redis_client.exists(cooldown_key)
            if not cooldown_active:
                # Cooldown expired! Transition to HALF_OPEN to test the waters
                await redis_client.set(state_key, HALF_OPEN)
                return HALF_OPEN

        return state

    async def record_failure(self, provider_name: str):
        """Called when an API request fails."""
        failure_key = f"cb:failures:{provider_name}"
        state_key = f"cb:state:{provider_name}"
        cooldown_key = f"cb:cooldown:{provider_name}"

        # Increment failure count
        failures = await redis_client.incr(failure_key)

        # If we hit the threshold, trip the breaker!
        if failures >= self.failure_threshold:
            await redis_client.set(state_key, OPEN)
            # Set a temporary key that expires after `cooldown_seconds`
            await redis_client.setex(
                cooldown_key, self.cooldown_seconds, "cooling_down"
            )

    async def record_success(self, provider_name: str):
        """Called when an API request succeeds."""
        failure_key = f"cb:failures:{provider_name}"
        state_key = f"cb:state:{provider_name}"

        # Reset everything back to healthy
        await redis_client.set(state_key, CLOSED)
        await redis_client.delete(failure_key)
