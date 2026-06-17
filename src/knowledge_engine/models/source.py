from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from knowledge_engine.models.base import Base, TimestampMixin, UUIDMixin
import enum

class SourceType(str, enum.Enum):
    TELEGRAM = "telegram"
    URL = "url"

class Source(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "sources"
    type: Mapped[SourceType] = mapped_column(
        SAEnum(SourceType, name="source_type", create_constraint=True), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_sync: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
