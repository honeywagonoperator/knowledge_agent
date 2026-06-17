from uuid import UUID
from knowledge_engine.db.session import AsyncSession; from knowledge_engine.db.repository import Repository
from knowledge_engine.models.source import Source, SourceType
from knowledge_engine.connectors.base import SyncResult; from knowledge_engine.connectors.url import URLConnector
from knowledge_engine.extractors.knowledge import KnowledgeExtractor
from knowledge_engine.extractors.graph import GraphExtractor

class SyncService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session; self._source_repo = Repository(session, Source)
    async def add_source(self, url: str, type: str, name: str | None = None) -> Source:
        source = Source(type=SourceType(type), name=name or url, url=url)
        return await self._source_repo.add(source)
    async def sync_source(self, source_id: UUID) -> SyncResult:
        source = await self._source_repo.get(source_id)
        if source is None: raise ValueError(f"Source {source_id} not found")
        connector = self._get_connector(source); result = await connector.sync()
        # Extraction pipeline
        extractor = KnowledgeExtractor(self._session)
        units_created = await extractor.extract_from_source(source_id)
        if units_created > 0:
            graph = GraphExtractor(self._session); await graph.extract_from_source(source_id)
        return result
    def _get_connector(self, source: Source) -> URLConnector:
        if source.type == SourceType.URL: return URLConnector(source, self._session)
        if source.type == SourceType.TELEGRAM: raise NotImplementedError("Telegram connector not yet implemented")
        raise ValueError(f"Unknown source type: {source.type}")
