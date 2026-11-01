from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models import CacheEntry


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def get_cache(session: AsyncSession, key: str) -> str | None:
    result = await session.execute(
        select(CacheEntry).where(CacheEntry.key == key, CacheEntry.expires_at > _now())
    )
    entry = result.scalar_one_or_none()
    return entry.value if entry else None


async def set_cache(session: AsyncSession, key: str, value: str, ttl_seconds: int) -> None:
    await session.merge(
        CacheEntry(key=key, value=value, expires_at=_now() + timedelta(seconds=ttl_seconds))
    )
    await session.commit()
