import html
import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InputMediaPhoto, Message

from bot.db.game_repo import save_game_result
from bot.db.session import async_session
from bot.db.user_repo import get_or_create_user
from bot.keyboards.game import play_kb, result_kb, vote_kb
from bot.services.achievements import check_new_badges
from bot.services.battle import BattleDish, build_battle
from bot.services.meals import ServiceUnavailable
from bot.states.game import GameStates

router = Router()
logger = logging.getLogger(__name__)


def fmt(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def pack(dish: BattleDish) -> dict:
    # В FSM кладём только простые данные (строки и числа)
    return {
        "name": dish.name,
        "views": dish.views,
        "meal_id": dish.meal.id,
        "photo": dish.meal.image_url,
    }


async def drop_buttons(message: Message) -> None:
    try:
        await message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass


async def send_battle(message: Message, state: FSMContext) -> None:
    try:
        battle = await build_battle()
    except ServiceUnavailable:
        await message.answer(
            "😔 Сервис временно недоступен. Попробуйте чуть позже.",
            reply_markup=play_kb("🔄 Попробовать снова"),
        )
        return

    a, b = pack(battle.a), pack(battle.b)
    await state.set_state(GameStates.waiting_vote)
    await state.update_data(battle={"a": a, "b": b})

    try:
        await message.answer_media_group(
            [
                InputMediaPhoto(media=a["photo"], caption=f"🅰 {a['name']}"),
                InputMediaPhoto(media=b["photo"], caption=f"🅱 {b['name']}"),
            ]
        )
    except TelegramBadRequest:
        logger.warning("Could not send battle photos")  # играем и без фото

    await message.answer(
        "<b>Какое блюдо популярнее?</b>\n"
        "<i>Считаем по числу просмотров статьи в Википедии за год.</i>",
        reply_markup=vote_kb(a["name"], b["name"]),
    )


@router.message(Command("play"))
async def cmd_play(message: Message, state: FSMContext):
    await send_battle(message, state)


@router.callback_query(F.data == "game:next")
async def on_next(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await drop_buttons(callback.message)
    await send_battle(callback.message, state)


@router.callback_query(GameStates.waiting_vote, F.data.in_({"vote:a", "vote:b"}))
async def on_vote(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    battle = data.get("battle")
    if not battle:
        await callback.answer("Этот бой уже завершён.", show_alert=True)
        return

    # Сбрасываем состояние сразу, чтобы двойной клик не засчитался дважды
    await state.clear()
    await callback.answer()
    await drop_buttons(callback.message)

    a, b = battle["a"], battle["b"]
    choice = callback.data.split(":")[1]
    winner = "a" if a["views"] >= b["views"] else "b"

    async with async_session() as session:
        user, _ = await get_or_create_user(
            session, callback.from_user.id, callback.from_user.username
        )
        is_correct, xp_earned, leveled_up = await save_game_result(
            session, user, a["name"], b["name"], choice, winner
        )
        total_xp, level = user.xp, user.level
        new_badges = await check_new_badges(session, user)

    logger.info("User %s answered correct=%s", callback.from_user.id, is_correct)

    win = a if winner == "a" else b
    win_name = win["name"]
    lines = [
        "<b>Верно!</b>" if is_correct else "<b>Не угадали.</b>",
        "",
        f"🅰 {html.escape(a['name'])}: {fmt(a['views'])}",
        f"🅱 {html.escape(b['name'])}: {fmt(b['views'])}",
        f"🏆 Популярнее: <b>{html.escape(win_name)}</b>",
        "",
        f"+{xp_earned} XP (всего {total_xp}, уровень {level})",
    ]
    if leveled_up:
        lines.append(f"🎉 <b>Новый уровень: {level}!</b>")
    for badge in new_badges:
        lines.append(f"{badge.emoji} Новый бейдж: <b>{html.escape(badge.title)}</b>")

    await callback.message.answer("\n".join(lines), reply_markup=result_kb(win["meal_id"]))


@router.callback_query(F.data.startswith("vote:"))
async def on_stale_vote(callback: CallbackQuery):
    # Нажали кнопку из старого боя (состояния уже нет)
    await callback.answer("Этот бой уже завершён. Нажмите «Следующий бой».", show_alert=True)
