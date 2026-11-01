from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models import UserAchievement


async def get_badge_codes(session: AsyncSession, user_id: int) -> set[str]:
    result = await session.execute(
        select(UserAchievement.code).where(UserAchievement.user_id == user_id)
    )
    return set(result.scalars())


def add_badge(session: AsyncSession, user_id: int, code: str) -> None:
    session.add(UserAchievement(user_id=user_id, code=code))
