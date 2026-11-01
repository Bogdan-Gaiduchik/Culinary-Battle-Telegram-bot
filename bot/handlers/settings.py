import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.db.session import async_session
from bot.db.user_repo import get_or_create_user, reset_progress, toggle_notifications
from bot.keyboards.game import play_kb
from bot.keyboards.settings import confirm_reset_kb, settings_kb

router = Router()
logger = logging.getLogger(__name__)


def settings_text(notifications: bool) -> str:
    state = "включены" if notifications else "выключены"
    return f"<b>Настройки</b>\n\nУведомления: <b>{state}</b>"


async def safe_edit(message: Message, text: str, markup) -> None:
    try:
        await message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest:
        pass  # например, текст не изменился


@router.message(Command("settings"))
async def cmd_settings(message: Message):
    async with async_session() as session:
        user, _ = await get_or_create_user(
            session, message.from_user.id, message.from_user.username
        )
    await message.answer(
        settings_text(user.notifications_enabled),
        reply_markup=settings_kb(user.notifications_enabled),
    )


@router.callback_query(F.data == "settings:toggle")
async def on_toggle(callback: CallbackQuery):
    await callback.answer()
    async with async_session() as session:
        user, _ = await get_or_create_user(
            session, callback.from_user.id, callback.from_user.username
        )
        enabled = await toggle_notifications(session, user)
    await safe_edit(callback.message, settings_text(enabled), settings_kb(enabled))


@router.callback_query(F.data == "settings:reset")
async def on_reset(callback: CallbackQuery):
    await callback.answer()
    await safe_edit(
        callback.message,
        "<b>Сбросить прогресс?</b>\n\nБудут удалены XP, уровень, история боёв, бейджи и ваши бои для друзей."
        "Это нельзя отменить.",
        confirm_reset_kb(),
    )


@router.callback_query(F.data == "settings:reset_yes")
async def on_reset_yes(callback: CallbackQuery):
    await callback.answer()
    async with async_session() as session:
        user, _ = await get_or_create_user(
            session, callback.from_user.id, callback.from_user.username
        )
        await reset_progress(session, user)
    logger.info("User %s reset progress", callback.from_user.id)
    await safe_edit(callback.message, "Прогресс сброшен. Начнём заново!", play_kb())


@router.callback_query(F.data == "settings:reset_no")
async def on_reset_no(callback: CallbackQuery):
    await callback.answer()
    async with async_session() as session:
        user, _ = await get_or_create_user(
            session, callback.from_user.id, callback.from_user.username
        )
    await safe_edit(
        callback.message,
        settings_text(user.notifications_enabled),
        settings_kb(user.notifications_enabled),
    )
