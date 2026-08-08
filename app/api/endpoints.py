import time
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import ChatRequest, LLMResponse
from app.models.domain import APIKey, RequestLog
from app.db.database import get_db
from app.api.dependencies import get_current_api_key
from app.core.rate_limit import RateLimiter
from app.core.router import FallbackRouter

# We create an APIRouter to organize our endpoints
router = APIRouter()

# Instantiate our core services
rate_limiter = RateLimiter()
fallback_router = FallbackRouter()


@router.post("/v1/chat/completions", response_model=LLMResponse)
async def chat_completions(
    request: ChatRequest,
    api_key: APIKey = Depends(get_current_api_key),
    db: AsyncSession = Depends(get_db),
):
    # 1. Rate Limiting Check
    # Convert requests per minute to tokens per second for our Lua script
    refill_rate = float(api_key.rate_limit_requests_per_minute) / 60.0

    is_allowed = await rate_limiter.is_allowed(
        api_key=str(api_key.id),
        max_requests=int(float(api_key.rate_limit_requests_per_minute)),
        refill_rate=refill_rate,
    )

    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Try again later.",
        )

    # 2. Route the Request & Measure Latency
    start_time = time.time()
    try:
        response = await fallback_router.route_request(request)
        error_msg = None
        status_code = 200
    except Exception as e:
        response = None
        error_msg = str(e)
        status_code = 500

    latency_ms = int((time.time() - start_time) * 1000)

    # 3. Log the Request to the Database
    log_entry = RequestLog(
        api_key_id=api_key.id,
        provider_used=response.provider if response else "failed",
        model_used=response.model if response else "unknown",
        prompt_tokens=response.prompt_tokens if response else 0,
        completion_tokens=response.completion_tokens if response else 0,
        total_tokens=response.total_tokens if response else 0,
        latency_ms=latency_ms,
        status_code=status_code,
        error_message=error_msg,
    )
    db.add(log_entry)
    await db.commit()

    # 4. Return the result or raise the final error
    if error_msg or not response:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Gateway routing failed: {error_msg}",
        )

    return response
