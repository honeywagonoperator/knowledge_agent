from uuid import UUID
from collections.abc import Sequence
from knowledge_engine.models.knowledge_unit import KnowledgeUnit
from knowledge_engine.models.document import Document


class ContextBuilder:
    @staticmethod
    def build(
        query: str,
        vector_results: Sequence[KnowledgeUnit],
        graph_results: dict[str, Sequence[KnowledgeUnit]],
    ) -> str:
        parts: list[str] = [f"## User Question
{query}
"]

        if vector_results:
            parts.append("## Relevant Knowledge Units (vector search)")
            for i, unit in enumerate(vector_results, 1):
                parts.append(f"
### Unit {i} (confidence: {unit.confidence:.2f})")
                parts.append(f"Domain: {unit.domain}")
                parts.append(unit.content[:500])

        if graph_results:
            parts.append("
## Graph Connections")
            for entity_id, units in graph_results.items():
                parts.append(f"
### Entity: {entity_id}")
                for unit in units:
                    parts.append(f"- {unit.content[:200]}")

        return "
".join(parts)

    @staticmethod
    def format_sources(
        vector_results: Sequence[KnowledgeUnit],
        graph_results: dict[str, Sequence[KnowledgeUnit]],
    ) -> list[dict]:
        seen_urls: set[str] = set()
        sources: list[dict] = []

        for unit in vector_results:
            if unit.document and unit.document.url not in seen_urls:
                seen_urls.add(unit.document.url)
                sources.append({
                    "url": unit.document.url,
                    "title": unit.document.title,
                    "snippet": unit.content[:200],
                })

        return sources
