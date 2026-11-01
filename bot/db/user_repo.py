from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models import CustomBattle, CustomBattleVote, GameHistory, User, UserAchievement


async def get_or_create_user(
    session: AsyncSession, telegram_id: int, username: str | None
) -> tuple[User, bool]:
    """Возвращает (пользователь, создан_ли_только_что)."""
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()

    if user is not None:
        if user.username != username:
            user.username = username
            await session.commit()
        return user, False

    user = User(telegram_id=telegram_id, username=username)
    session.add(user)
    await session.commit()
    return user, True


async def get_top(session: AsyncSession, limit: int = 10) -> list[User]:
    result = await session.execute(
        select(User).where(User.xp > 0).order_by(User.xp.desc(), User.id).limit(limit)
    )
    return list(result.scalars())


async def get_rank(session: AsyncSession, user: User) -> int:
    result = await session.execute(
        select(func.count()).select_from(User).where(User.xp > user.xp)
    )
    return result.scalar_one() + 1


async def toggle_notifications(session: AsyncSession, user: User) -> bool:
    user.notifications_enabled = not user.notifications_enabled
    await session.commit()
    return user.notifications_enabled


async def reset_progress(session: AsyncSession, user: User) -> None:
    own_battles = select(CustomBattle.id).where(CustomBattle.creator_id == user.id)
    await session.execute(
        delete(CustomBattleVote).where(CustomBattleVote.battle_id.in_(own_battles))
    )
    await session.execute(delete(CustomBattleVote).where(CustomBattleVote.user_id == user.id))
    await session.execute(delete(CustomBattle).where(CustomBattle.creator_id == user.id))
    await session.execute(delete(GameHistory).where(GameHistory.user_id == user.id))
    await session.execute(delete(UserAchievement).where(UserAchievement.user_id == user.id))
    user.xp = 0
    user.level = 1
    await session.commit()
