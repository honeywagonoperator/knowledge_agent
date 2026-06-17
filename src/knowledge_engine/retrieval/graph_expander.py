from uuid import UUID
from collections.abc import Sequence, Set as AbstractSet
from sqlalchemy import select, or_, and_
from knowledge_engine.db.session import AsyncSession
from knowledge_engine.models.entity import Entity
from knowledge_engine.models.relation import Relation
from knowledge_engine.models.knowledge_unit import KnowledgeUnit


class GraphExpander:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def extract_entities(self, text: str) -> Sequence[Entity]:
        text_lower = text.lower()
        result = await self._session.execute(
            select(Entity).where(Entity.name.ilike(f"%{text_lower}%"))
        )
        return result.scalars().all()

    async def expand(
        self, entity_ids: Sequence[str], depth: int = 1
    ) -> dict[str, Sequence[KnowledgeUnit]]:
        result: dict[str, Sequence[KnowledgeUnit]] = {}
        visited: set[str] = set()
        current_level: set[str] = set(entity_ids)

        for _ in range(depth):
            if not current_level:
                break
            visited.update(current_level)

            rel_result = await self._session.execute(
                select(Relation).where(
                    or_(
                        Relation.from_entity_id.in_(current_level),
                        Relation.to_entity_id.in_(current_level),
                    )
                )
            )
            relations: Sequence[Relation] = rel_result.scalars().all()

            next_level: set[str] = set()
            for rel in relations:
                for eid in (rel.from_entity_id, rel.to_entity_id):
                    if eid not in visited:
                        next_level.add(eid)
                        ku_result = await self._session.execute(
                            select(KnowledgeUnit).where(
                                KnowledgeUnit.id == rel.source_knowledge_unit_id
                            )
                        )
                        ku = ku_result.scalar_one_or_none()
                        if ku is not None:
                            result.setdefault(eid, []).append(ku)

            current_level = next_level

        return result
