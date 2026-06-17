from datetime import datetime
import uuid
from sqlalchemy import String, Text, Float, ForeignKey, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from knowledge_engine.models.base import Base, UUIDMixin
import enum

class RelationType(str, enum.Enum):
    DEPENDS_ON = "depends_on"
    IMPLEMENTS = "implements"
    RELATES_TO = "relates_to"
    PART_OF = "part_of"
    CONTRARY_TO = "contrary_to"

class Relation(UUIDMixin, Base):
    __tablename__ = "relations"

    from_entity_id: Mapped[str] = mapped_column(
        String(500),
        ForeignKey("entities.id", ondelete="CASCADE"),
        nullable=False,
    )
    to_entity_id: Mapped[str] = mapped_column(
        String(500),
        ForeignKey("entities.id", ondelete="CASCADE"),
        nullable=False,
    )
    relation_type: Mapped[RelationType] = mapped_column(
        SAEnum(RelationType, name="relation_type", create_constraint=True),
        nullable=False,
    )
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    source_knowledge_unit_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_units.id", ondelete="SET NULL"),
        nullable=True,
    )
    source_quote: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
