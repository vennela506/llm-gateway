import secrets
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.domain import APIKey
from app.api.dependencies import hash_api_key

# Create a router specifically for admin endpoints
router = APIRouter(prefix="/admin", tags=["Admin"])


class KeyCreateRequest(BaseModel):
    name: str
    rate_limit_requests_per_minute: int = 60


@router.post("/keys")
async def create_api_key(request: KeyCreateRequest, db: AsyncSession = Depends(get_db)):
    """Generates a new Gateway API Key."""

    raw_key = f"gw-{secrets.token_urlsafe(32)}"
    hashed_key = hash_api_key(raw_key)

    new_key = APIKey(
        name=request.name,
        hashed_key=hashed_key,
        rate_limit_requests_per_minute=request.rate_limit_requests_per_minute,
    )
    db.add(new_key)
    await db.commit()

    return {
        "name": request.name,
        "api_key": raw_key,
        "message": "Save this key securely! You will not be able to see it again.",
    }
