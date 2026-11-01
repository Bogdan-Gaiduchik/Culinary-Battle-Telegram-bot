import html

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.db.achievement_repo import get_badge_codes
from bot.db.game_repo import get_stats
from bot.db.session import async_session
from bot.db.user_repo import get_or_create_user, get_rank, get_top
from bot.keyboards.game import play_kb
from bot.services.achievements import BADGES
from bot.services.progress import XP_PER_LEVEL

router = Router()

MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}


@router.message(Command("profile"))
async def cmd_profile(message: Message):
    async with async_session() as session:
        user, _ = await get_or_create_user(
            session, message.from_user.id, message.from_user.username
        )
        total, correct = await get_stats(session, user.id)
        rank = await get_rank(session, user)
        codes = await get_badge_codes(session, user.id)

    in_level = user.xp % XP_PER_LEVEL
    filled = in_level * 10 // XP_PER_LEVEL
    bar = "▰" * filled + "▱" * (10 - filled)
    accuracy = round(correct * 100 / total) if total else 0

    earned = [b for b in BADGES.values() if b.code in codes]
    if earned:
        badges_text = "\n".join(
            f"{b.emoji} <b>{html.escape(b.title)}</b>: {html.escape(b.description)}"
            for b in earned
        )
    else:
        badges_text = "Пока нет. Сыграйте бой!"

    text = (
        "<b>Ваш профиль</b>\n\n"
        f"Уровень: <b>{user.level}</b>\n"
        f"{bar} {in_level}/{XP_PER_LEVEL} XP до следующего\n"
        f"Всего XP: <b>{user.xp}</b>\n"
        f"Место в рейтинге: <b>#{rank}</b>\n\n"
        f"Боёв сыграно: <b>{total}</b>, верных: <b>{correct}</b> ({accuracy}%)\n\n"
        f"🏅 <b>Бейджи ({len(earned)}/{len(BADGES)})</b>\n{badges_text}"
    )
    await message.answer(text, reply_markup=play_kb())


@router.message(Command("top"))
async def cmd_top(message: Message):
    async with async_session() as session:
        user, _ = await get_or_create_user(
            session, message.from_user.id, message.from_user.username
        )
        top = await get_top(session, 10)
        rank = await get_rank(session, user)

    if not top:
        await message.answer("Пока никто не играл. Станьте первым!", reply_markup=play_kb())
        return

    lines = ["🏆 <b>Топ-10 игроков</b>\n"]
    for place, u in enumerate(top, start=1):
        name = html.escape(u.username) if u.username else f"Игрок #{u.id}"
        mark = " (вы)" if u.id == user.id else ""
        lines.append(f"{MEDALS.get(place, f'{place}.')} {name}{mark}: {u.xp} XP, ур. {u.level}")

    if user.id not in {u.id for u in top}:
        lines.append(f"\nВаше место: <b>#{rank}</b> ({user.xp} XP)")

    await message.answer("\n".join(lines), reply_markup=play_kb())
