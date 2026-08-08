from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.core.config import settings

# Create the async engine
engine = create_async_engine(settings.database_url, echo=False)

# Create a session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

# Base class for our SQLAlchemy models
Base = declarative_base()


# Dependency to inject DB sessions into our FastAPI endpoints later
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
