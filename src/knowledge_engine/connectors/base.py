from dataclasses import dataclass, field; from uuid import UUID
@dataclass
class SyncResult: source_id: UUID; documents_created: int = 0; documents_skipped: int = 0; errors: list[str] = field(default_factory=list)
