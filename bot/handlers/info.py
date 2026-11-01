from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.keyboards.game import menu_kb
from bot.texts import INFO_PARTS

router = Router()


@router.message(Command("info", "help"))
async def cmd_info(message: Message):
    for i, part in enumerate(INFO_PARTS):
        markup = menu_kb() if i == len(INFO_PARTS) - 1 else None
        await message.answer(part, reply_markup=markup)
