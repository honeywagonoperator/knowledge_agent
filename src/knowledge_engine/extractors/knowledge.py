from uuid import UUID; from collections.abc import Sequence
from sqlalchemy import select
from knowledge_engine.db.session import AsyncSession; from knowledge_engine.db.repository import Repository
from knowledge_engine.models.document import Document; from knowledge_engine.models.knowledge_unit import KnowledgeUnit

class KnowledgeExtractor:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session; self._doc_repo = Repository(session, Document); self._unit_repo = Repository(session, KnowledgeUnit)
    async def extract_from_source(self, source_id: UUID) -> int:
        result = await self._session.execute(select(Document).where(Document.source_id == source_id))
        documents: Sequence[Document] = result.scalars().all(); total = 0
        for doc in documents: total += await self._extract_from_document(doc)
        return total
    async def _extract_from_document(self, document: Document) -> int:
        chunks = self._chunk_text(document.content); count = 0
        for chunk in chunks:
            unit = await self._create_knowledge_unit(document, chunk)
            if unit is not None: self._session.add(unit); count += 1
        if count: await self._session.flush()
        return count
    def _chunk_text(self, text: str, max_chars: int = 2000) -> list[str]:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]; chunks: list[str] = []; current = ""
        for para in paragraphs:
            if len(current) + len(para) < max_chars: current = f"{current}\n\n{para}" if current else para
            else:
                if current: chunks.append(current)
                current = para
        if current: chunks.append(current)
        return chunks
    async def _create_knowledge_unit(self, document: Document, chunk: str) -> KnowledgeUnit | None:
        return KnowledgeUnit(document_id=document.id, type="text_chunk", content=chunk, domain="general", confidence=0.5)
