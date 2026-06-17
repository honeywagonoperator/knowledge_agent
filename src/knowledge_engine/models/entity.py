from datetime import datetime
from sqlalchemy import String, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from knowledge_engine.models.base import Base
import enum

class EntityType(str, enum.Enum):
    CONCEPT = "concept"; PERSON = "person"; TOOL = "tool"; METHOD = "method"; LIBRARY = "library"

class Entity(Base):
    __tablename__ = "entities"
    id: Mapped[str] = mapped_column(String(500), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    type: Mapped[EntityType] = mapped_column(SAEnum(EntityType, name="entity_type", create_constraint=True), nullable=False)
    canonical: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
