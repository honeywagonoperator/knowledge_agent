from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


class Repository[T]:
    def __init__(self, session: AsyncSession, model: type[T]) -> None: self._session = session; self._model = model
    async def add(self, instance: T) -> T: self._session.add(instance); await self._session.flush(); return instance
    async def get(self, id: UUID | str) -> T | None: return await self._session.get(self._model, id, populate_existing=True)
    async def list(self, skip: int = 0, limit: int = 100) -> Sequence[T]:
        stmt = select(self._model).offset(skip).limit(limit); result = await self._session.execute(stmt); return result.scalars().all()
    async def count(self) -> int:
        stmt = select(func.count()).select_from(self._model); result = await self._session.execute(stmt); return result.scalar_one()
    async def delete(self, instance: T) -> None: await self._session.delete(instance); await self._session.flush()
