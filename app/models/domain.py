import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base


# Helper function to get modern UTC time without the timezone metadata
def get_utc_now_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)  # e.g., "Frontend App", "Data Science Team"
    hashed_key = Column(String, unique=True, nullable=False, index=True)

    # Rate limiting configs specific to this key
    rate_limit_requests_per_minute = Column(Integer, default=60)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=get_utc_now_naive)

    # Relationship to the logs
    logs = relationship("RequestLog", back_populates="api_key_record")


class RequestLog(Base):
    __tablename__ = "request_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    api_key_id = Column(String, ForeignKey("api_keys.id"), nullable=False)

    # Request metadata
    provider_used = Column(String, nullable=False)  # e.g., "openai"
    model_used = Column(String, nullable=False)

    # Metrics
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    cost = Column(Float, default=0.0)  # Calculated based on provider pricing
    latency_ms = Column(Integer, default=0)

    # Status
    status_code = Column(Integer, default=200)
    error_message = Column(String, nullable=True)

    created_at = Column(DateTime, default=get_utc_now_naive)

    # Relationship back to the API Key
    api_key_record = relationship("APIKey", back_populates="logs")
