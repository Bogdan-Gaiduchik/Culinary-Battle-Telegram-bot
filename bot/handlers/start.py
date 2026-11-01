import logging
import re

from aiogram import Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.db.session import async_session
from bot.db.user_repo import get_or_create_user
from bot.handlers.friends import open_shared_battle
from bot.keyboards.game import menu_kb

router = Router()
logger = logging.getLogger(__name__)

BATTLE_ARG = re.compile(r"^battle_(\d{1,9})$")


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, state: FSMContext):
    await state.clear()
    tg_user = message.from_user
    async with async_session() as session:
        user, created = await get_or_create_user(
            session, tg_user.id, tg_user.username
        )

    # В лог пишем только id, без имени и текста сообщений
    logger.info("User %s %s", tg_user.id, "registered" if created else "returned")

    # Переход по ссылке-приглашению: t.me/<бот>?start=battle_<id>
    if command.args:
        match = BATTLE_ARG.match(command.args)
        if match:
            await open_shared_battle(message, int(match.group(1)))
            return

    if created:
        text = (
            "Добро пожаловать в <b>Кулинарную Битву</b>!\n"
            "Вы зарегистрированы. Я показываю два блюда, а вы угадываете, какое "
            "из них популярнее.\n\n"
            "📖 Подробная инструкция для новичков: /info"
        )
    else:
        text = (
            f"С возвращением! 👋\n"
            f"Ваш уровень: <b>{user.level}</b>, опыт: <b>{user.xp} XP</b>.\n\n"
            "Инструкция: /info"
        )
    await message.answer(text, reply_markup=menu_kb())
