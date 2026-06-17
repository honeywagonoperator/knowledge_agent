from uuid import UUID
from collections.abc import Sequence
from sqlalchemy import select, text
from pgvector.sqlalchemy import Vector
from knowledge_engine.db.session import AsyncSession
from knowledge_engine.models.knowledge_unit import KnowledgeUnit


class VectorRetriever:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def search(
        self, embedding: list[float], top_k: int = 5
    ) -> Sequence[KnowledgeUnit]:
        embedding_vec = Vector(embedding)
        stmt = (
            select(KnowledgeUnit)
            .where(KnowledgeUnit.embedding.isnot(None))
            .order_by(KnowledgeUnit.embedding.cosine_distance(embedding_vec))
            .limit(top_k)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def search_by_text(
        self, text: str, top_k: int = 5
    ) -> Sequence[KnowledgeUnit]:
        stmt = (
            select(KnowledgeUnit)
            .where(KnowledgeUnit.content.ilike(f"%{text}%"))
            .limit(top_k)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()
