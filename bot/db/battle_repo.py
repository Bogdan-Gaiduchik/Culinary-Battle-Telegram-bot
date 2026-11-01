from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models import CustomBattle, CustomBattleVote, User
from bot.services.progress import XP_VOTE, calc_level


async def create_battle(
    session: AsyncSession,
    creator_id: int,
    dish_a: str,
    dish_b: str,
    meal_id_a: str | None,
    meal_id_b: str | None,
) -> CustomBattle:
    battle = CustomBattle(
        creator_id=creator_id,
        dish_a=dish_a,
        dish_b=dish_b,
        meal_id_a=meal_id_a,
        meal_id_b=meal_id_b,
    )
    session.add(battle)
    await session.commit()
    return battle


async def get_battle(session: AsyncSession, battle_id: int) -> CustomBattle | None:
    return await session.get(CustomBattle, battle_id)


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)


async def has_voted(session: AsyncSession, battle_id: int, user_id: int) -> bool:
    result = await session.execute(
        select(CustomBattleVote.id).where(
            CustomBattleVote.battle_id == battle_id, CustomBattleVote.user_id == user_id
        )
    )
    return result.first() is not None


async def add_vote(
    session: AsyncSession, battle: CustomBattle, user: User, choice: str
) -> bool:
    """False, если пользователь уже голосовал. После False объекты сессии не используем."""
    session.add(CustomBattleVote(battle_id=battle.id, user_id=user.id, choice=choice))
    user.xp += XP_VOTE
    user.level = calc_level(user.xp)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        return False
    return True


async def get_counts(session: AsyncSession, battle_id: int) -> tuple[int, int]:
    result = await session.execute(
        select(CustomBattleVote.choice, func.count())
        .where(CustomBattleVote.battle_id == battle_id)
        .group_by(CustomBattleVote.choice)
    )
    counts = {choice: n for choice, n in result.all()}
    return counts.get("a", 0), counts.get("b", 0)


async def close_battle(session: AsyncSession, battle: CustomBattle) -> None:
    battle.status = "closed"
    await session.commit()


async def get_voter_telegram_ids(session: AsyncSession, battle_id: int) -> list[int]:
    """Telegram ID проголосовавших, у которых включены уведомления."""
    result = await session.execute(
        select(User.telegram_id)
        .join(CustomBattleVote, CustomBattleVote.user_id == User.id)
        .where(
            CustomBattleVote.battle_id == battle_id,
            User.notifications_enabled.is_(True),
        )
    )
    return list(result.scalars())


async def count_created(session: AsyncSession, user_id: int) -> int:
    result = await session.execute(
        select(func.count()).select_from(CustomBattle).where(CustomBattle.creator_id == user_id)
    )
    return result.scalar_one()
