import hashlib
import os
from datetime import UTC

from knowledge_engine.connectors.base import BaseConnector, SyncResult
from knowledge_engine.db.session import AsyncSession
from knowledge_engine.models.document import Document
from knowledge_engine.models.source import Source


class TelegramConnector(BaseConnector):
    def __init__(self, source: Source, session: AsyncSession) -> None:
        super().__init__(source)
        self._session = session

    async def sync(self) -> SyncResult:
        result = SyncResult(source_id=self.source.id)
        api_id = os.getenv("TELEGRAM_API_ID")
        api_hash = os.getenv("TELEGRAM_API_HASH")

        if not api_id or not api_hash:
            result.errors.append(
                "TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in env"
            )
            return result

        channel = self._parse_channel(self.source.url)

        try:
            from telethon import TelegramClient

            async with TelegramClient("knowledge_agent_session", int(api_id), api_hash) as client:
                entity = await client.get_entity(channel)
                async for message in client.iter_messages(entity, limit=100):
                    if not message.text:
                        continue

                    content_hash = hashlib.sha256(
                        message.text.encode()
                    ).hexdigest()

                    from sqlalchemy import select
                    existing = await self._session.execute(
                        select(Document).where(
                            Document.content_hash == content_hash
                        )
                    )
                    if existing.scalar_one_or_none():
                        result.documents_skipped += 1
                        continue

                    message_link = (
                        f"https://t.me/{channel}/{message.id}"
                    )
                    title = message.date.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )

                    doc = Document(
                        source_id=self.source.id,
                        title=title,
                        content=message.text,
                        url=message_link,
                        content_hash=content_hash,
                    )
                    self._session.add(doc)
                    await self._session.flush()
                    result.documents_created += 1

        except Exception as e:
            result.errors.append(f"Telegram sync failed: {e}")

        from datetime import datetime
        self.source.last_sync = datetime.now(UTC)
        return result

    @staticmethod
    def _parse_channel(url: str) -> str:
        url = url.rstrip("/")
        parts = url.split("/")
        return parts[-1] if parts else url
