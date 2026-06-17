from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession as SASession, async_sessionmaker
from knowledge_engine.db.engine import get_engine

AsyncSession = SASession

def async_session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), class_=AsyncSession, expire_on_commit=False)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    factory = async_session_factory()
    async with factory() as session:
        yield session
