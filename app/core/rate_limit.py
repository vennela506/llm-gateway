import time
from app.core.redis import redis_client

# This Lua script runs atomically inside Redis.
# It checks how much time has passed, adds new tokens to the bucket,
# and checks if we have enough tokens to allow the request.
TOKEN_BUCKET_LUA = """
local key = KEYS[1]
local max_tokens = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2]) -- tokens per second
local requested = tonumber(ARGV[3])
local now = tonumber(ARGV[4])

-- Get current bucket state
local bucket = redis.call('HMGET', key, 'tokens', 'last_update')
local tokens = tonumber(bucket[1])
local last_update = tonumber(bucket[2])

-- If bucket doesn't exist, initialize it full
if not tokens then
    tokens = max_tokens
    last_update = now
end

-- Refill tokens based on time passed
local elapsed = math.max(0, now - last_update)
tokens = math.min(max_tokens, tokens + (elapsed * refill_rate))

-- Check if we have enough tokens
if tokens >= requested then
    -- Consume tokens
    tokens = tokens - requested
    redis.call('HMSET', key, 'tokens', tokens, 'last_update', now)
    redis.call('EXPIRE', key, math.ceil(max_tokens / refill_rate) * 2)
    return 1 -- 1 means Allowed
else
    -- Not enough tokens, just update the state
    redis.call('HMSET', key, 'tokens', tokens, 'last_update', now)
    redis.call('EXPIRE', key, math.ceil(max_tokens / refill_rate) * 2)
    return 0 -- 0 means Denied (Rate Limited)
end
"""


class RateLimiter:
    async def is_allowed(
        self, api_key: str, max_requests: int, refill_rate: float
    ) -> bool:
        """
        Returns True if the request is allowed, False if rate limited.
        """
        redis_key = f"rate_limit:requests:{api_key}"
        now = time.time()

        # We use standard .eval() which is still 100% atomic,
        # but avoids the evalsha testing bugs on Windows!
        # The arguments are: script, number_of_keys, keys..., args...
        result = await redis_client.eval(
            TOKEN_BUCKET_LUA, 1, redis_key, max_requests, refill_rate, 1, now
        )

        return result == 1
