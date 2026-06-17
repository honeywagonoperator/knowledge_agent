import os
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from knowledge_engine.connectors.base import BaseConnector, SyncResult
from knowledge_engine.connectors.sync_service import SyncService
from knowledge_engine.connectors.telegram import TelegramConnector
from knowledge_engine.connectors.url import URLConnector
from knowledge_engine.index import KnowledgeIndex
from knowledge_engine.models.document import Document
from knowledge_engine.models.source import Source, SourceType


class AsyncIter:
    def __init__(self, items):
        self.items = list(items)
    def __aiter__(self):
        return self
    async def __anext__(self):
        if not self.items:
            raise StopAsyncIteration
        return self.items.pop(0)


def make_source(url: str = "https://test.com") -> Source:
    return Source(id=uuid.uuid4(), type=SourceType.URL, name="Test", url=url, enabled=True)


# ── BaseConnector ──────────────────────────────────────────────────────────────


def test_base_not_implemented():
    connector = BaseConnector(make_source())
    with pytest.raises(NotImplementedError):
        import asyncio
        asyncio.run(connector.sync())


# ── URLConnector ───────────────────────────────────────────────────────────────


async def test_url_successful_fetch(db_session):
    src = make_source()
    db_session.add(src)
    await db_session.flush()
    html = "<html><title>Hello World</title><body><p>Content</p></body></html>"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "text/html"}
    mock_response.text = html

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.aclose = AsyncMock()

    with patch("httpx.AsyncClient", return_value=mock_client):
        connector = URLConnector(src, db_session)
        result = await connector.sync()

    assert result.documents_created == 1
    assert result.documents_skipped == 0
    assert len(result.errors) == 0
    assert src.last_sync is not None


async def test_url_non_html_content_type(db_session):
    src = make_source()
    db_session.add(src)
    await db_session.flush()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "application/pdf"}
    mock_response.text = "%PDF-1.4 fake content"

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.aclose = AsyncMock()

    with patch("httpx.AsyncClient", return_value=mock_client):
        connector = URLConnector(src, db_session)
        result = await connector.sync()

    assert result.documents_created == 0
    assert len(result.errors) == 1
    assert "Failed to fetch" in result.errors[0]


async def test_url_strips_boilerplate(db_session):
    src = make_source()
    db_session.add(src)
    await db_session.flush()
    html = (
        "<html><title>Test</title><body>"
        "<script>alert('bad')</script>"
        "<style>.css{color:red}</style>"
        "<nav>menu</nav><footer>copyright</footer>"
        "<p>Real content</p>"
        "</body></html>"
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "text/html"}
    mock_response.text = html

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.aclose = AsyncMock()

    with patch("httpx.AsyncClient", return_value=mock_client):
        connector = URLConnector(src, db_session)
        result = await connector.sync()

    assert result.documents_created == 1
    from knowledge_engine.db.repository import Repository
    repo = Repository(db_session, Document)
    docs = await repo.list()
    assert len(docs) == 1
    assert "alert" not in docs[0].content
    assert ".css" not in docs[0].content
    assert "Real content" in docs[0].content


async def test_url_dedup_by_hash(db_session):
    src = make_source()
    db_session.add(src)
    await db_session.flush()
    html = "<html><body><p>Same content</p></body></html>"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "text/html"}
    mock_response.text = html

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.aclose = AsyncMock()

    with patch("httpx.AsyncClient", return_value=mock_client):
        connector = URLConnector(src, db_session)
        result1 = await connector.sync()
        result2 = await connector.sync()

    assert result1.documents_created == 1
    assert result2.documents_skipped == 1


async def test_url_http_error(db_session):
    src = make_source()
    db_session.add(src)
    await db_session.flush()
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=Exception("HTTP 404"))
    mock_client.aclose = AsyncMock()

    with patch("httpx.AsyncClient", return_value=mock_client):
        connector = URLConnector(src, db_session)
        result = await connector.sync()

    assert result.documents_created == 0
    assert len(result.errors) == 1


async def test_url_network_error(db_session):
    src = make_source()
    db_session.add(src)
    await db_session.flush()
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=Exception("Connection refused"))
    mock_client.aclose = AsyncMock()

    with patch("httpx.AsyncClient", return_value=mock_client):
        connector = URLConnector(src, db_session)
        result = await connector.sync()

    assert result.documents_created == 0
    assert len(result.errors) == 1
    assert "Connection refused" in result.errors[0]


async def test_url_updates_last_sync(db_session):
    src = make_source()
    db_session.add(src)
    await db_session.flush()
    html = "<html><body><p>Content</p></body></html>"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "text/html"}
    mock_response.text = html

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.aclose = AsyncMock()

    with patch("httpx.AsyncClient", return_value=mock_client):
        connector = URLConnector(src, db_session)
        assert src.last_sync is None
        await connector.sync()
        assert src.last_sync is not None


# ── TelegramConnector ──────────────────────────────────────────────────────────


async def test_telegram_missing_env_vars(db_session):
    src = Source(id=uuid.uuid4(), type=SourceType.TELEGRAM, name="TG", url="https://t.me/channel", enabled=True)
    with patch.object(os, "getenv", return_value=None):
        connector = TelegramConnector(src, db_session)
        result = await connector.sync()

    assert result.documents_created == 0
    assert len(result.errors) == 1
    assert "TELEGRAM_API_ID" in result.errors[0]


def test_telegram_parse_channel():
    assert TelegramConnector._parse_channel("https://t.me/mychannel") == "mychannel"
    assert TelegramConnector._parse_channel("https://t.me/mychannel/") == "mychannel"
    assert TelegramConnector._parse_channel("mychannel") == "mychannel"


async def test_telegram_successful_sync(db_session):
    src = Source(id=uuid.uuid4(), type=SourceType.TELEGRAM, name="TG", url="https://t.me/channel", enabled=True)
    db_session.add(src)
    await db_session.flush()
    message_date = datetime.now(timezone.utc)

    mock_message = MagicMock()
    mock_message.text = "Telegram message content"
    mock_message.id = 42
    mock_message.date = message_date

    mock_client = AsyncMock()
    mock_client.get_entity = AsyncMock(return_value="channel_entity")
    mock_client.iter_messages = MagicMock(return_value=AsyncIter([mock_message]))

    with (
        patch.object(os, "getenv", side_effect=lambda k, d=None: {"TELEGRAM_API_ID": "12345", "TELEGRAM_API_HASH": "abcdef"}.get(k, d)),
        patch("telethon.TelegramClient") as mock_tg_class,
    ):
        mock_tg_class.return_value.__aenter__.return_value = mock_client
        connector = TelegramConnector(src, db_session)
        result = await connector.sync()

    assert result.documents_created == 1
    assert result.documents_skipped == 0
    assert len(result.errors) == 0
    assert src.last_sync is not None


async def test_telegram_dedup(db_session):
    src = Source(id=uuid.uuid4(), type=SourceType.TELEGRAM, name="TG", url="https://t.me/channel", enabled=True)
    db_session.add(src)
    await db_session.flush()
    message_date = datetime.now(timezone.utc)

    mock_message = MagicMock()
    mock_message.text = "Dedup content"
    mock_message.id = 42
    mock_message.date = message_date

    mock_client = AsyncMock()
    mock_client.get_entity = AsyncMock(return_value="channel_entity")
    mock_client.iter_messages = MagicMock(return_value=AsyncIter([mock_message, mock_message]))

    with (
        patch.object(os, "getenv", side_effect=lambda k, d=None: {"TELEGRAM_API_ID": "12345", "TELEGRAM_API_HASH": "abcdef"}.get(k, d)),
        patch("telethon.TelegramClient") as mock_tg_class,
    ):
        mock_tg_class.return_value.__aenter__.return_value = mock_client
        connector = TelegramConnector(src, db_session)
        result = await connector.sync()

    assert result.documents_created == 1
    assert result.documents_skipped == 1


async def test_telegram_error_handling(db_session):
    src = Source(id=uuid.uuid4(), type=SourceType.TELEGRAM, name="TG", url="https://t.me/channel", enabled=True)

    mock_client = AsyncMock()
    mock_client.get_entity = AsyncMock(side_effect=Exception("Channel not found"))

    with (
        patch.object(os, "getenv", side_effect=lambda k, d=None: {"TELEGRAM_API_ID": "12345", "TELEGRAM_API_HASH": "abcdef"}.get(k, d)),
        patch("telethon.TelegramClient") as mock_tg_class,
    ):
        mock_tg_class.return_value.__aenter__.return_value = mock_client
        connector = TelegramConnector(src, db_session)
        result = await connector.sync()

    assert result.documents_created == 0
    assert len(result.errors) == 1
    assert "Channel not found" in result.errors[0]


# ── SyncService ────────────────────────────────────────────────────────────────


async def test_sync_service_calls_index(db_session):
    src = make_source("https://sync-test.com")
    from knowledge_engine.db.repository import Repository
    repo = Repository(db_session, Source)
    await repo.add(src)

    doc = Document(
        id=uuid.uuid4(), source_id=src.id,
        title="Sync Doc", content="Sync content",
        url="https://sync-test.com/doc", content_hash="sync_hash",
    )
    doc_repo = Repository(db_session, Document)
    await doc_repo.add(doc)

    mock_connector = AsyncMock()
    mock_connector.sync = AsyncMock(return_value=SyncResult(source_id=src.id, documents_created=1))
    mock_connector.source = src

    mock_index = MagicMock(spec=KnowledgeIndex)
    mock_index.insert_document = MagicMock()
    mock_index.persist = MagicMock()

    service = SyncService(db_session, mock_index)
    result = await service.sync_source(mock_connector)

    assert result.documents_created == 1
    mock_connector.sync.assert_awaited_once()
    mock_index.insert_document.assert_called_once_with(
        doc_id=str(doc.id),
        content=doc.content,
        metadata={"url": doc.url, "title": doc.title},
    )
    mock_index.persist.assert_called_once()
