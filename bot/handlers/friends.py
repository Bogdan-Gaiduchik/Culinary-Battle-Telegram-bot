import html
import logging
import re
from urllib.parse import quote

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.db.battle_repo import (
    add_vote,
    close_battle,
    create_battle,
    get_battle,
    get_counts,
    get_user_by_id,
    get_voter_telegram_ids,
    has_voted,
)
from bot.db.session import async_session
from bot.db.user_repo import get_or_create_user
from bot.keyboards.friends import finished_kb, friend_vote_kb, owner_kb
from bot.keyboards.game import menu_kb
from bot.services.achievements import check_new_badges
from bot.services.meals import ServiceUnavailable, meal_service
from bot.services.progress import XP_VOTE
from bot.states.friends import FriendBattleStates
from bot.utils.validators import clean_dish_name

router = Router()
logger = logging.getLogger(__name__)

CVOTE_RE = re.compile(r"^cvote:(\d{1,9}):([ab])$")
OWNER_RE = re.compile(r"^cb:(status|finish):(\d{1,9})$")

BAD_NAME = (
    "Это не похоже на название блюда. Используйте буквы и цифры, "
    "от 2 до 40 символов. Попробуйте ещё раз (или /cancel)."
)


def esc(text: str) -> str:
    return html.escape(text)


async def find_meal_id(name: str) -> str | None:
    """Ищем блюдо в TheMealDB, чтобы у победителя был рецепт. Не нашли: не страшно."""
    try:
        meals = await meal_service.search(name)
    except ServiceUnavailable:
        return None
    return meals[0].id if meals else None


async def make_links(bot: Bot, battle) -> tuple[str, str]:
    me = await bot.me()
    link = f"https://t.me/{me.username}?start=battle_{battle.id}"
    text = f"Что популярнее: {battle.dish_a} или {battle.dish_b}? Голосуй!"
    share = f"https://t.me/share/url?url={quote(link, safe='')}&text={quote(text, safe='')}"
    return link, share


def result_text(battle, votes_a: int, votes_b: int) -> tuple[str, str | None]:
    """Текст итогов и meal_id победителя (если известен)."""
    lines = [
        "🏁 <b>Итоги боя</b>",
        "",
        f"🅰 {esc(battle.dish_a)}: <b>{votes_a}</b>",
        f"🅱 {esc(battle.dish_b)}: <b>{votes_b}</b>",
        "",
    ]
    if votes_a == votes_b:
        lines.append("🤝 Ничья!" if votes_a else "Никто не проголосовал.")
        return "\n".join(lines), None

    if votes_a > votes_b:
        name, meal_id = battle.dish_a, battle.meal_id_a
    else:
        name, meal_id = battle.dish_b, battle.meal_id_b
    lines.append(f"🏆 Победило: <b>{esc(name)}</b>")
    return "\n".join(lines), meal_id


async def safe_edit(message: Message, text: str) -> None:
    try:
        await message.edit_text(text)  # без reply_markup кнопки убираются
    except TelegramBadRequest:
        pass


# ---------- Создание боя ----------

async def start_creation(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(FriendBattleStates.entering_dish_a)
    await message.answer(
        "👥 <b>Бой для друзей</b>\n\n"
        "Введите название <b>первого</b> блюда, например: <i>Борщ</i>.\n"
        "Для отмены отправьте /cancel"
    )


@router.message(Command("newbattle"))
async def cmd_newbattle(message: Message, state: FSMContext):
    await start_creation(message, state)


@router.callback_query(F.data == "friends:new")
async def on_friends_new(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await start_creation(callback.message, state)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    if await state.get_state() is None:
        await message.answer("Отменять нечего.", reply_markup=menu_kb())
        return
    await state.clear()
    await message.answer("Отменено.", reply_markup=menu_kb())


@router.message(FriendBattleStates.entering_dish_a, F.text)
async def on_dish_a(message: Message, state: FSMContext):
    name = clean_dish_name(message.text)
    if not name:
        await message.answer(BAD_NAME)
        return
    await state.update_data(dish_a=name)
    await state.set_state(FriendBattleStates.entering_dish_b)
    await message.answer(
        f"Первое блюдо: <b>{esc(name)}</b>\n\nТеперь введите название <b>второго</b> блюда."
    )


@router.message(FriendBattleStates.entering_dish_b, F.text)
async def on_dish_b(message: Message, state: FSMContext):
    name = clean_dish_name(message.text)
    if not name:
        await message.answer(BAD_NAME)
        return

    data = await state.get_data()
    dish_a = data.get("dish_a")
    if not dish_a:  # на случай потери состояния
        await state.clear()
        await message.answer("Что-то пошло не так, начнём заново: /newbattle")
        return
    if name.casefold() == dish_a.casefold():
        await message.answer("Блюда должны быть разными. Введите другое название.")
        return

    meal_a = await find_meal_id(dish_a)
    meal_b = await find_meal_id(name)

    async with async_session() as session:
        user, _ = await get_or_create_user(
            session, message.from_user.id, message.from_user.username
        )
        battle = await create_battle(session, user.id, dish_a, name, meal_a, meal_b)
        new_badges = await check_new_badges(session, user)

    await state.clear()
    logger.info("User %s created battle %s", message.from_user.id, battle.id)

    link, share = await make_links(message.bot, battle)
    lines = [
        "<b>Бой создан!</b>",
        "",
        f"🅰 {esc(dish_a)}  vs  🅱 {esc(name)}",
        "",
        "Отправьте друзьям эту ссылку:",
        link,
        "",
        "Когда друзья проголосуют, нажмите «Завершить бой». "
        "За свой бой голосовать нельзя.",
    ]
    for badge in new_badges:
        lines.append(f"\n{badge.emoji} Новый бейдж: <b>{esc(badge.title)}</b>")

    await message.answer("\n".join(lines), reply_markup=owner_kb(battle.id, share))


@router.message(StateFilter(FriendBattleStates.entering_dish_a, FriendBattleStates.entering_dish_b))
async def on_not_text(message: Message):
    await message.answer("Отправьте название блюда обычным текстом (или /cancel).")


# ---------- Переход по ссылке-приглашению ----------

async def open_shared_battle(message: Message, battle_id: int) -> None:
    async with async_session() as session:
        user, _ = await get_or_create_user(
            session, message.from_user.id, message.from_user.username
        )
        battle = await get_battle(session, battle_id)
        if battle is None:
            await message.answer("😔 Такой бой не найден.", reply_markup=menu_kb())
            return
        creator = await get_user_by_id(session, battle.creator_id)
        voted = await has_voted(session, battle.id, user.id)
        votes_a, votes_b = await get_counts(session, battle.id)
        is_owner = user.id == battle.creator_id

    if battle.status == "closed":
        text, meal_id = result_text(battle, votes_a, votes_b)
        await message.answer(text, reply_markup=finished_kb(meal_id))
        return

    if is_owner:
        _, share = await make_links(message.bot, battle)
        await message.answer(
            f"Это ваш бой: <b>{esc(battle.dish_a)}</b> vs <b>{esc(battle.dish_b)}</b>.\n"
            "Отправьте ссылку друзьям, а когда они проголосуют, завершите бой.",
            reply_markup=owner_kb(battle.id, share),
        )
        return

    if voted:
        await message.answer(
            "Вы уже проголосовали в этом бое. Итоги придут, когда автор его завершит.",
            reply_markup=menu_kb(),
        )
        return

    author = f"@{esc(creator.username)}" if creator and creator.username else "вашего друга"
    await message.answer(
        f"👥 <b>Бой от {author}</b>\n\n"
        f"Какое блюдо вы выберете: <b>{esc(battle.dish_a)}</b> или <b>{esc(battle.dish_b)}</b>?",
        reply_markup=friend_vote_kb(battle.id, battle.dish_a, battle.dish_b),
    )


# ---------- Голосование ----------

@router.callback_query(F.data.regexp(CVOTE_RE))
async def on_cvote(callback: CallbackQuery):
    match = CVOTE_RE.match(callback.data)
    battle_id, choice = int(match.group(1)), match.group(2)

    async with async_session() as session:
        user, _ = await get_or_create_user(
            session, callback.from_user.id, callback.from_user.username
        )
        battle = await get_battle(session, battle_id)
        if battle is None or battle.status != "open":
            await callback.answer("Этот бой уже завершён или не найден.", show_alert=True)
            return
        if user.id == battle.creator_id:
            await callback.answer("За свой бой голосовать нельзя.", show_alert=True)
            return
        dish = battle.dish_a if choice == "a" else battle.dish_b
        ok = await add_vote(session, battle, user, choice)

    if not ok:
        await callback.answer("Вы уже голосовали в этом бое.", show_alert=True)
        return

    logger.info("User %s voted in battle %s", callback.from_user.id, battle_id)
    await callback.answer("Голос принят!")
    await safe_edit(
        callback.message,
        f"Ваш голос за <b>{esc(dish)}</b> принят! +{XP_VOTE} XP\n\n"
        "Итоги пришлю, когда автор завершит бой.",
    )


# ---------- Управление боем (автор) ----------

@router.callback_query(F.data.regexp(OWNER_RE))
async def on_owner_action(callback: CallbackQuery):
    match = OWNER_RE.match(callback.data)
    action, battle_id = match.group(1), int(match.group(2))

    async with async_session() as session:
        user, _ = await get_or_create_user(
            session, callback.from_user.id, callback.from_user.username
        )
        battle = await get_battle(session, battle_id)
        if battle is None or battle.creator_id != user.id:
            await callback.answer("Это не ваш бой.", show_alert=True)
            return

        votes_a, votes_b = await get_counts(session, battle_id)

        if action == "status":
            await callback.answer(
                f"🅰 {battle.dish_a}: {votes_a}\n🅱 {battle.dish_b}: {votes_b}\n"
                f"Всего голосов: {votes_a + votes_b}",
                show_alert=True,
            )
            return

        if battle.status == "closed":
            await callback.answer("Этот бой уже завершён.", show_alert=True)
            return

        await close_battle(session, battle)
        voter_ids = await get_voter_telegram_ids(session, battle_id)

    text, meal_id = result_text(battle, votes_a, votes_b)
    markup = finished_kb(meal_id)

    await callback.answer()
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass
    await callback.message.answer(text, reply_markup=markup)

    # Рассылаем итоги всем, кто голосовал
    for tg_id in voter_ids:
        try:
            await callback.bot.send_message(tg_id, text, reply_markup=markup)
        except (TelegramForbiddenError, TelegramBadRequest):
            continue
    logger.info("Battle %s finished, voters=%s", battle_id, len(voter_ids))
