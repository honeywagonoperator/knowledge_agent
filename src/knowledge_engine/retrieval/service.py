from dataclasses import dataclass, field
from collections.abc import Sequence
from knowledge_engine.db.session import AsyncSession
from knowledge_engine.retrieval.vector import VectorRetriever
from knowledge_engine.retrieval.graph_expander import GraphExpander
from knowledge_engine.retrieval.context_builder import ContextBuilder


@dataclass
class SourceRef:
    url: str
    title: str
    snippet: str


@dataclass
class AnswerResult:
    answer: str
    sources: list[SourceRef] = field(default_factory=list)


class RetrievalService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._vector = VectorRetriever(session)
        self._graph = GraphExpander(session)
        self._builder = ContextBuilder()

    async def query(
        self, question: str, expand: bool = True, depth: int = 1
    ) -> AnswerResult:
        # 1. Vector search (fallback to text search)
        vector_results = await self._vector.search_by_text(question)

        # 2. Entity extraction + graph expansion
        graph_results: dict[str, Sequence] = {}
        if expand:
            entities = await self._graph.extract_entities(question)
            if entities:
                entity_ids = [e.id for e in entities]
                graph_results = await self._graph.expand(entity_ids, depth=depth)

        # 3. Build context
        context = self._builder.build(question, vector_results, graph_results)

        # 4. TODO: LLM synthesis (will use Ollama/LlamaIndex in production)
        answer = self._fallback_answer(question, context)

        # 5. Format sources
        raw_sources = self._builder.format_sources(vector_results, graph_results)
        sources = [SourceRef(**s) for s in raw_sources]

        return AnswerResult(answer=answer, sources=sources)

    def _fallback_answer(self, question: str, context: str) -> str:
        lines = context.split("\n")
        relevant = [l for l in lines if l.strip() and not l.startswith("#")]
        if relevant:
            return (
                f"Based on the knowledge base, I found information related to "
                f"your question about '{question}'.\n\n"
                f"Relevant context:\n{relevant[0][:500]}"
            )
        return (
            f"I don't have enough information in the knowledge base to answer "
            f"about '{question}'. Try adding a source first with `ke add-source`."
        )
