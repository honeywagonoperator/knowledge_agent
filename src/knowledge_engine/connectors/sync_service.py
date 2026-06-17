from uuid import UUID
from knowledge_engine.models.source import Source
class SyncService:
    async def add_source(self, url: str, type: str, name: str | None = None) -> Source: raise NotImplementedError
    async def sync_source(self, source_id: UUID) -> None: raise NotImplementedError
