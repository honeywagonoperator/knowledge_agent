from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from knowledge_engine.db.config import DatabaseConfig

_engine: AsyncEngine | None = None

def create_engine(config: DatabaseConfig | None = None) -> AsyncEngine:
    global _engine
    config = config or DatabaseConfig()
    _engine = create_async_engine(config.dsn, echo=False, pool_size=5, max_overflow=10)
    return _engine

def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_engine()
    return _engine

async def dispose_engine() -> None:
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
