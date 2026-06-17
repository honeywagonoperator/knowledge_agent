from dataclasses import dataclass, field; from uuid import UUID
from knowledge_engine.models.source import Source
@dataclass
class SyncResult: source_id: UUID; documents_created: int = 0; documents_skipped: int = 0; errors: list[str] = field(default_factory=list)
class BaseConnector:
    source: Source
    def __init__(self, source: Source) -> None: self.source = source
    async def sync(self) -> SyncResult: raise NotImplementedError
