from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.conf.config import settings

engine = create_async_engine(settings.DB_URL)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
