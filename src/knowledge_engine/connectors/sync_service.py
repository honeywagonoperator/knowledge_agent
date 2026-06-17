from uuid import UUID
from knowledge_engine.db.session import AsyncSession; from knowledge_engine.db.repository import Repository
from knowledge_engine.models.source import Source, SourceType
from knowledge_engine.connectors.base import SyncResult

class SyncService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session; self._source_repo = Repository(session, Source)
    async def add_source(self, url: str, type: str, name: str | None = None) -> Source:
        source = Source(type=SourceType(type), name=name or url, url=url)
        return await self._source_repo.add(source)
    async def sync_source(self, source_id: UUID) -> SyncResult:
        raise NotImplementedError("Run ke sync on feat/knowledge-extraction branch")
