from dataclasses import dataclass, field
@dataclass
class SourceRef: url: str; title: str; snippet: str
@dataclass
class AnswerResult: answer: str; sources: list[SourceRef] = field(default_factory=list)
class RetrievalService:
    async def query(self, question: str, expand: bool = True, depth: int = 1) -> AnswerResult:
        return AnswerResult(answer=f"Query not yet implemented. Run 'ke query' on feat/hybrid-retrieval branch for the full pipeline.\nQuestion: {question}")
