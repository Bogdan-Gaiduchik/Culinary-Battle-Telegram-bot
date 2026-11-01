from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def play_kb(text: str = "Играть") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=text, callback_data="game:next")]]
    )


def vote_kb(name_a: str, name_b: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"🅰 {name_a}", callback_data="vote:a")],
            [InlineKeyboardButton(text=f"🅱 {name_b}", callback_data="vote:b")],
        ]
    )

def result_kb(meal_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📖 Рецепт победителя", callback_data=f"recipe:{meal_id}")],
            [InlineKeyboardButton(text="🔄 Следующий бой", callback_data="game:next")],
        ]
    )

def menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⚔️ Играть", callback_data="game:next")],
            [InlineKeyboardButton(text="👥 Бой с друзьями", callback_data="friends:new")],
        ]
    )
