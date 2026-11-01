from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.achievement_repo import add_badge, get_badge_codes
from bot.db.battle_repo import count_created
from bot.db.game_repo import get_stats, last_results
from bot.models import User


@dataclass(frozen=True)
class Badge:
    code: str
    emoji: str
    title: str
    description: str


BADGES: dict[str, Badge] = {
    b.code: b
    for b in [
        Badge("first_game", "🍳", "Первый бой", "Сыграйте свой первый бой"),
        Badge("streak_5", "🔥", "Серия из 5", "5 верных ответов подряд"),
        Badge("correct_10", "👨‍🍳", "Знаток", "10 верных ответов"),
        Badge("correct_50", "⭐", "Шеф-эксперт", "50 верных ответов"),
        Badge("organizer", "🎪", "Организатор", "Создайте бой для друзей"),
    ]
}


async def check_new_badges(session: AsyncSession, user: User) -> list[Badge]:
    """Проверяет условия, выдаёт новые бейджи и возвращает только что полученные."""
    owned = await get_badge_codes(session, user.id)
    total, correct = await get_stats(session, user.id)
    last5 = await last_results(session, user.id, 5)
    created = await count_created(session, user.id)

    conditions = {
        "first_game": total >= 1,
        "streak_5": len(last5) == 5 and all(last5),
        "correct_10": correct >= 10,
        "correct_50": correct >= 50,
        "organizer": created >= 1,
    }

    new = []
    for badge in BADGES.values():
        if conditions.get(badge.code) and badge.code not in owned:
            add_badge(session, user.id, badge.code)
            new.append(badge)
    if new:
        await session.commit()
    return new
