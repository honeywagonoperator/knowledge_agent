import uuid

import pytest
from sqlalchemy import select

from knowledge_engine.db.repository import Repository
from knowledge_engine.models.source import Source, SourceType
from knowledge_engine.models.document import Document


pytestmark = pytest.mark.asyncio


async def test_add_and_get(db_session):
    repo = Repository(db_session, Source)
    src = Source(id=uuid.uuid4(), type=SourceType.URL, name="Test", url="https://test.com", enabled=True)
    created = await repo.add(src)
    assert created.id == src.id
    assert created.name == "Test"

    fetched = await repo.get(src.id)
    assert fetched is not None
    assert fetched.name == "Test"
    assert fetched.url == "https://test.com"


async def test_add_duplicate_raises(db_session):
    repo = Repository(db_session, Source)
    src = Source(id=uuid.uuid4(), type=SourceType.URL, name="Test", url="https://test.com", enabled=True)
    await repo.add(src)
    src2 = Source(id=src.id, type=SourceType.URL, name="Test 2", url="https://test2.com", enabled=True)
    with pytest.raises(Exception):
        await repo.add(src2)
        await db_session.commit()


async def test_list(db_session):
    repo = Repository(db_session, Source)
    src1 = Source(id=uuid.uuid4(), type=SourceType.URL, name="A", url="https://a.com", enabled=True)
    src2 = Source(id=uuid.uuid4(), type=SourceType.URL, name="B", url="https://b.com", enabled=True)
    await repo.add(src1)
    await repo.add(src2)

    items = await repo.list()
    assert len(items) >= 2


async def test_list_with_pagination(db_session):
    repo = Repository(db_session, Source)
    src1 = Source(id=uuid.uuid4(), type=SourceType.URL, name="Page1", url="https://p1.com", enabled=True)
    src2 = Source(id=uuid.uuid4(), type=SourceType.URL, name="Page2", url="https://p2.com", enabled=True)
    await repo.add(src1)
    await repo.add(src2)

    items = await repo.list(limit=1)
    assert len(items) == 1


async def test_count(db_session):
    repo = Repository(db_session, Source)
    before = await repo.count()
    src = Source(id=uuid.uuid4(), type=SourceType.URL, name="Count", url="https://count.com", enabled=True)
    await repo.add(src)
    after = await repo.count()
    assert after == before + 1


async def test_get_not_found(db_session):
    repo = Repository(db_session, Source)
    result = await repo.get(uuid.uuid4())
    assert result is None


async def test_delete(db_session):
    repo = Repository(db_session, Source)
    src = Source(id=uuid.uuid4(), type=SourceType.URL, name="Del", url="https://del.com", enabled=True)
    await repo.add(src)
    await repo.delete(src)
    fetched = await repo.get(src.id)
    assert fetched is None


async def test_cascade_delete(db_session):
    source_repo = Repository(db_session, Source)
    doc_repo = Repository(db_session, Document)

    src = Source(id=uuid.uuid4(), type=SourceType.URL, name="Cascade", url="https://cascade.com", enabled=True)
    await source_repo.add(src)

    doc = Document(
        id=uuid.uuid4(), source_id=src.id,
        title="Doc", content="Text", url="https://cascade.com/doc",
        content_hash="hash_cascade",
    )
    await doc_repo.add(doc)

    await source_repo.delete(src)
    await db_session.commit()

    fetched = await doc_repo.get(doc.id)
    assert fetched is None
