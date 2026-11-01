from sqlalchemy.ext.asyncio import AsyncSession

from bot.models import GameHistory, User
from sqlalchemy import func, select
from bot.services.progress import XP_CORRECT, XP_PARTICIPATION, calc_level


async def save_game_result(
    session: AsyncSession,
    user: User,
    dish_a: str,
    dish_b: str,
    choice: str,
    winner: str,
) -> tuple[bool, int, bool]:
    """Возвращает (угадал, полученный XP, повысился ли уровень)."""
    is_correct = choice == winner
    xp_earned = XP_CORRECT if is_correct else XP_PARTICIPATION

    old_level = user.level
    user.xp += xp_earned
    user.level = calc_level(user.xp)

    session.add(
        GameHistory(
            user_id=user.id,
            dish_a=dish_a,
            dish_b=dish_b,
            user_choice=choice,
            correct_winner=winner,
            is_correct=is_correct,
            xp_earned=xp_earned,
        )
    )
    await session.commit()
    return is_correct, xp_earned, user.level > old_level



async def get_stats(session: AsyncSession, user_id: int) -> tuple[int, int]:
    """Возвращает (всего боёв, верных ответов)."""
    total = (
        await session.execute(
            select(func.count()).select_from(GameHistory).where(GameHistory.user_id == user_id)
        )
    ).scalar_one()
    correct = (
        await session.execute(
            select(func.count())
            .select_from(GameHistory)
            .where(GameHistory.user_id == user_id, GameHistory.is_correct.is_(True))
        )
    ).scalar_one()
    return total, correct


async def last_results(session: AsyncSession, user_id: int, limit: int) -> list[bool]:
    """Результаты последних боёв, от новых к старым."""
    result = await session.execute(
        select(GameHistory.is_correct)
        .where(GameHistory.user_id == user_id)
        .order_by(GameHistory.id.desc())
        .limit(limit)
    )
    return list(result.scalars())
