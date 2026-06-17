
from knowledge_engine.connectors.base import BaseConnector, SyncResult
from knowledge_engine.db.repository import Repository
from knowledge_engine.db.session import AsyncSession
from knowledge_engine.index import KnowledgeIndex
from knowledge_engine.models.document import Document


class SyncService:
    def __init__(self, session: AsyncSession, index: KnowledgeIndex) -> None:
        self._session = session
        self._index = index

    async def sync_source(self, connector: BaseConnector) -> SyncResult:
        result = await connector.sync()
        doc_repo = Repository(self._session, Document)
        docs = await doc_repo.list()
        for doc in docs:
            if doc.source_id == result.source_id and doc.id:
                self._index.insert_document(
                    doc_id=str(doc.id),
                    content=doc.content,
                    metadata={"url": doc.url, "title": doc.title},
                )
        self._index.persist()
        return result
