from contextlib import asynccontextmanager
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import settings
from app.core.redis import check_redis_connection
from app.api import endpoints, admin
from app.core.logger import setup_logging, logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize our JSON logger
    setup_logging()
    logger.info("startup", message="Starting up LLM Gateway...")

    # 2. Check Redis connection
    await check_redis_connection()

    yield

    # 3. Shutdown sequence
    logger.info("shutdown", message="Shutting down LLM Gateway...")


# Initialize the FastAPI application
app = FastAPI(
    title="LLM Gateway",
    description="A production-grade LLM Gateway with rate limiting, fallbacks, and cost tracking.",
    version="1.0.0",
    lifespan=lifespan,
)

# --- Setup Prometheus Metrics ---
Instrumentator().instrument(app).expose(app, include_in_schema=True)

# Include our API routers
app.include_router(endpoints.router, tags=["Gateway"])
app.include_router(admin.router)


@app.get("/health", tags=["System"])
async def health_check():
    """Simple health check endpoint to confirm the API is running."""
    return {"status": "healthy", "environment": settings.environment}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.port, reload=True)
