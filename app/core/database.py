from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# Determine database URL
database_url = settings.database_url
if not database_url:
    # Use SQLite for development
    database_url = "sqlite+aiosqlite:///./smartpc.db"

# Create async engine
engine = create_async_engine(
    database_url,
    echo=True,
    future=True,
    connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


# Dependency to get DB session
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

