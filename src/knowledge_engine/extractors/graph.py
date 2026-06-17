from uuid import UUID
import re
from collections.abc import Sequence
from sqlalchemy import select
from knowledge_engine.db.session import AsyncSession
from knowledge_engine.db.repository import Repository
from knowledge_engine.models.knowledge_unit import KnowledgeUnit
from knowledge_engine.models.entity import Entity, EntityType
from knowledge_engine.models.relation import Relation, RelationType


class GraphExtractor:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._entity_repo = Repository(session, Entity)
        self._relation_repo = Repository(session, Relation)

    async def extract_from_source(self, source_id: UUID) -> None:
        result = await self._session.execute(
            select(KnowledgeUnit)
            .join(KnowledgeUnit.document)
            .where(KnowledgeUnit.document.has(source_id=source_id))
        )
        units: Sequence[KnowledgeUnit] = result.scalars().all()
        for unit in units:
            await self._extract_from_unit(unit)

    async def _extract_from_unit(self, unit: KnowledgeUnit) -> None:
        entities = self._extract_entities(unit.content)
        for entity_data in entities:
            entity = await self._entity_repo.get(entity_data["id"])
            if entity is None:
                entity = Entity(
                    id=entity_data["id"],
                    name=entity_data["name"],
                    type=EntityType(entity_data["type"]),
                    canonical=entity_data.get("canonical"),
                )
                await self._entity_repo.add(entity)

            pairs = self._extract_relations(unit.content, entity_data["id"], entity_data["name"])
            for pair in pairs:
                existing = await self._session.execute(
                    select(Relation).where(
                        Relation.from_entity_id == entity_data["id"],
                        Relation.to_entity_id == pair["to"],
                        Relation.source_knowledge_unit_id == unit.id,
                    )
                )
                if existing.scalar_one_or_none():
                    continue

                rel = Relation(
                    from_entity_id=entity_data["id"],
                    to_entity_id=pair["to"],
                    relation_type=RelationType(pair["type"]),
                    confidence=pair.get("confidence", 0.5),
                    weight=pair.get("weight", 1.0),
                    source_knowledge_unit_id=unit.id,
                    source_quote=pair.get("quote"),
                )
                await self._relation_repo.add(rel)

    def _extract_entities(self, text: str) -> list[dict]:
        entities: list[dict] = []
        seen: set[str] = set()

        patterns = [
            (r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b", EntityType.CONCEPT),
        ]

        for pattern, etype in patterns:
            for match in re.finditer(pattern, text):
                name = match.group(1)
                if len(name) < 3:
                    continue
                eid = name.lower().replace(" ", "_")
                if eid in seen:
                    continue
                seen.add(eid)
                entities.append({
                    "id": eid,
                    "name": name,
                    "type": etype.value,
                })

        return entities

    def _extract_relations(
        self, text: str, entity_id: str, entity_name: str
    ) -> list[dict]:
        relations: list[dict] = []
        text_lower = text.lower()

        relation_signals = [
            ("depends_on", ["depends on", "requires", "uses", "built on"]),
            ("implements", ["implements", "provides", "enables"]),
            ("part_of", ["part of", "component of", "belongs to"]),
            ("contrary_to", ["unlike", "in contrast to", "alternative to", "vs"]),
        ]

        sentences = re.split(r"[.!?]+", text_lower)
        for sentence in sentences:
            for rel_type_str, signals in relation_signals:
                for signal in signals:
                    if signal not in sentence:
                        continue
                    potential = re.findall(r"\b([a-z]+(?:\s+[a-z]+)*)\b", sentence)
                    for match in potential:
                        candidate = match.strip()
                        if (
                            candidate
                            and candidate != entity_name.lower()
                            and len(candidate) > 3
                        ):
                            cid = candidate.lower().replace(" ", "_")
                            relations.append({
                                "to": cid,
                                "type": rel_type_str,
                                "confidence": 0.5,
                                "weight": 1.0,
                                "quote": sentence.strip(),
                            })
                            break

        return relations
