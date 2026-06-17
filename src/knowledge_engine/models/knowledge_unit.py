import uuid
from sqlalchemy import String, Text, Float, ForeignKey; from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from knowledge_engine.models.base import Base, TimestampMixin, UUIDMixin
class KnowledgeUnit(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_units"
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String(100), nullable=False); content: Mapped[str] = mapped_column(Text, nullable=False)
    domain: Mapped[str] = mapped_column(String(100), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    embedding: Mapped[Vector | None] = mapped_column(Vector(1536), nullable=True)
