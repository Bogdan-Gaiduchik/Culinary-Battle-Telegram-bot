from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def friend_vote_kb(battle_id: int, dish_a: str, dish_b: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"🅰 {dish_a}", callback_data=f"cvote:{battle_id}:a")],
            [InlineKeyboardButton(text=f"🅱 {dish_b}", callback_data=f"cvote:{battle_id}:b")],
        ]
    )


def owner_kb(battle_id: int, share_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Поделиться с друзьями", url=share_url)],
            [InlineKeyboardButton(text="Текущий счёт", callback_data=f"cb:status:{battle_id}")],
            [InlineKeyboardButton(text="Завершить бой", callback_data=f"cb:finish:{battle_id}")],
        ]
    )


def finished_kb(meal_id: str | None) -> InlineKeyboardMarkup:
    rows = []
    if meal_id:
        rows.append(
            [InlineKeyboardButton(text="📖 Рецепт победителя", callback_data=f"recipe:{meal_id}")]
        )
    rows.append([InlineKeyboardButton(text="Сыграть", callback_data="game:next")])
    rows.append([InlineKeyboardButton(text="Свой бой для друзей", callback_data="friends:new")])
    return InlineKeyboardMarkup(inline_keyboard=rows)