from redis.asyncio import Redis
from app.core.config import settings

# We create a global Redis client that our app will use
redis_client = Redis.from_url(settings.redis_url, decode_responses=True)


async def check_redis_connection():
    """Ping Redis to ensure we are connected on startup."""
    try:
        await redis_client.ping()
        print("Successfully connected to Redis!")
    except Exception as e:
        print(f"Failed to connect to Redis: {e}")
