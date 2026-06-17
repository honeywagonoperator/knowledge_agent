import pytest
import pytest_asyncio
from sqlalchemy import text
from knowledge_engine.db.config import DatabaseConfig
from knowledge_engine.db.engine import create_engine, dispose_engine, get_engine
from knowledge_engine.db.session import async_session_factory
from knowledge_engine.models.base import Base


@pytest_asyncio.fixture
async def db_session():
    config = DatabaseConfig()
    engine = create_engine(config)
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.execute(text("DROP TABLE IF EXISTS knowledge_units, entities, relations CASCADE"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    factory = async_session_factory()
    async with factory() as session:
        yield session
        await session.rollback()

    await dispose_engine()
