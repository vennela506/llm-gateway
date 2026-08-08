import hashlib
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.database import get_db
from app.models.domain import APIKey

# This tells FastAPI to look for an Authorization Bearer token in the request header
security = HTTPBearer()


def hash_api_key(api_key: str) -> str:
    """Hashes the API key using SHA-256 for secure storage and lookup."""
    return hashlib.sha256(api_key.encode()).hexdigest()


async def get_current_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> APIKey:
    """
    Dependency that validates the Bearer token.
    If valid, returns the APIKey database record. If invalid, throws a 401 Unauthorized.
    """
    # 1. Extract the raw token from the header
    raw_token = credentials.credentials

    # 2. Hash it to match how we store it in the database
    hashed_token = hash_api_key(raw_token)

    # 3. Look it up in Postgres
    result = await db.execute(select(APIKey).where(APIKey.hashed_key == hashed_token))
    api_key_record = result.scalars().first()

    # 4. Reject if not found or deactivated
    if not api_key_record or not api_key_record.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, inactive, or missing API Key",
        )

    # 5. Pass the database record to the endpoint
    return api_key_record
