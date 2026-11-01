from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def settings_kb(notifications: bool) -> InlineKeyboardMarkup:
    label = "Уведомления: вкл" if notifications else "Уведомления: выкл"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data="settings:toggle")],
            [InlineKeyboardButton(text="🗑 Сбросить прогресс", callback_data="settings:reset")],
        ]
    )


def confirm_reset_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Да, сбросить", callback_data="settings:reset_yes"),
                InlineKeyboardButton(text="Отмена", callback_data="settings:reset_no"),
            ]
        ]
    )
