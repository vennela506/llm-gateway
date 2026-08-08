import pytest
import time
from fakeredis.aioredis import FakeRedis
from app.core.rate_limit import RateLimiter
from app.core import rate_limit


@pytest.fixture
async def rate_limiter(mocker):
    # Create a fake in-memory Redis server
    fake_redis = FakeRedis(decode_responses=True)

    # Patch the real redis_client with our fake one
    mocker.patch.object(rate_limit, "redis_client", fake_redis)

    # Initialize the rate limiter (it will register the Lua script on the fake redis)
    return RateLimiter()


async def test_token_bucket_burst_and_refill(rate_limiter):
    api_key = "test_user_123"
    max_requests = 3
    refill_rate = 1.0  # 1 token per second

    # 1. Burst Traffic: Send 3 requests instantly (should all be Allowed)
    for _ in range(3):
        allowed = await rate_limiter.is_allowed(api_key, max_requests, refill_rate)
        assert allowed is True

    # 2. Exceed Limit: The 4th request should be Denied (bucket is empty)
    allowed = await rate_limiter.is_allowed(api_key, max_requests, refill_rate)
    assert allowed is False

    # 3. Refill: Wait 1.1 seconds for 1 token to refill
    time.sleep(1.1)

    # 4. Success: This request should now be Allowed
    allowed = await rate_limiter.is_allowed(api_key, max_requests, refill_rate)
    assert allowed is True
