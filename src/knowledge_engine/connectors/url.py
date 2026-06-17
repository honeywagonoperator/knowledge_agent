import hashlib
import httpx; from bs4 import BeautifulSoup, Tag
from knowledge_engine.models.source import Source; from knowledge_engine.models.document import Document
from knowledge_engine.db.session import AsyncSession; from knowledge_engine.connectors.base import BaseConnector, SyncResult

class URLConnector(BaseConnector):
    def __init__(self, source: Source, session: AsyncSession) -> None:
        super().__init__(source); self._session = session
    async def sync(self) -> SyncResult:
        result = SyncResult(source_id=self.source.id)
        client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        try:
            for url in [self.source.url]:
                try:
                    doc = await self._fetch_and_parse(client, url)
                    if doc is None: result.errors.append(f"Failed to fetch: {url}"); continue
                    from sqlalchemy import select
                    existing = await self._session.execute(select(Document).where(Document.content_hash == doc.content_hash))
                    if existing.scalar_one_or_none(): result.documents_skipped += 1; continue
                    self._session.add(doc); await self._session.flush()
                    result.documents_created += 1
                except Exception as e: result.errors.append(f"{url}: {e}")
        finally: await client.aclose()
        from datetime import datetime, timezone; self.source.last_sync = datetime.now(timezone.utc)
        return result
    async def _fetch_and_parse(self, client: httpx.AsyncClient, url: str) -> Document | None:
        resp = await client.get(url); resp.raise_for_status()
        content_type = resp.headers.get("content-type", "")
        if "text/html" not in content_type and "text/plain" not in content_type: return None
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]): tag.decompose()
        title_tag = soup.find("title"); title = title_tag.get_text(strip=True) if isinstance(title_tag, Tag) else ""
        text = soup.get_text(separator="
", strip=True)
        content_hash = hashlib.sha256(text.encode()).hexdigest()
        return Document(source_id=self.source.id, title=title or url, content=text, url=url, content_hash=content_hash)
