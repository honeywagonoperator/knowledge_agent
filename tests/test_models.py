import uuid
from datetime import datetime, timezone
from knowledge_engine.models.source import Source, SourceType
from knowledge_engine.models.document import Document
from knowledge_engine.models.base import Base


def test_source_create():
    src = Source(
        type=SourceType.URL, name="Test Source", url="https://example.com",
        id=uuid.uuid4(), enabled=True,
    )
    assert src.type == SourceType.URL
    assert src.name == "Test Source"
    assert src.url == "https://example.com"
    assert src.enabled is True
    assert src.last_sync is None
    assert isinstance(src.id, uuid.UUID)


def test_source_type_enums():
    assert SourceType.TELEGRAM.value == "telegram"
    assert SourceType.URL.value == "url"


def test_source_default_enabled():
    src = Source(type=SourceType.TELEGRAM, name="TG", url="https://t.me/channel", enabled=True)
    assert src.enabled is True


def test_document_create():
    doc = Document(
        id=uuid.uuid4(),
        source_id=uuid.uuid4(),
        title="Test Doc",
        content="Hello world",
        url="https://example.com/doc",
        content_hash="abc123",
    )
    assert doc.title == "Test Doc"
    assert doc.content == "Hello world"
    assert doc.content_hash == "abc123"
    assert isinstance(doc.id, uuid.UUID)


def test_base_has_metadata():
    assert hasattr(Base, "metadata")
