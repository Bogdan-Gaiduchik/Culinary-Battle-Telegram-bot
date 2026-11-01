import html
import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery

from bot.keyboards.game import play_kb, result_kb
from bot.services.meals import Meal, ServiceUnavailable, meal_service
from bot.services.nutrition import nutrition_service

router = Router()
logger = logging.getLogger(__name__)


def split_text(text: str, limit: int = 3800) -> list[str]:
    """Режет длинный текст по абзацам: лимит Telegram 4096 символов."""
    text = text.replace("\r\n", "\n").strip()
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")

    parts, current = [], ""
    for paragraph in text.split("\n"):
        while len(paragraph) > limit:  # на случай абзаца длиннее лимита
            parts.append(paragraph[:limit])
            paragraph = paragraph[limit:]
        if len(current) + len(paragraph) + 1 > limit:
            parts.append(current)
            current = ""
        current += paragraph + "\n"
    if current.strip():
        parts.append(current)
    return parts


def build_header(meal: Meal, calories: int | None) -> str:
    lines = [
        f"🍽 <b>{html.escape(meal.name)}</b>",
        f"{html.escape(meal.category)} · {html.escape(meal.area)}",
        "",
    ]
    if calories is not None:
        lines.append(f"🔥 Калорийность: ~<b>{calories} ккал</b> на порцию (оценка)")
    else:
        lines.append("🔥 Калорийность сейчас недоступна")

    lines += ["", "🧾 <b>Ингредиенты</b>"]
    for name, measure in meal.ingredients:
        item = html.escape(name)
        lines.append(f"• {item} — {html.escape(measure)}" if measure else f"• {item}")

    if meal.youtube_url:
        url = html.escape(meal.youtube_url, quote=True)
        lines += ["", f'▶️ <a href="{url}">Видео-инструкция</a>']
    return "\n".join(lines)


@router.callback_query(F.data.startswith("recipe:"))
async def on_recipe(callback: CallbackQuery):
    meal_id = callback.data.split(":", 1)[1]
    if not meal_id.isdigit():  # callback_data приходит от клиента, проверяем
        await callback.answer()
        return
    await callback.answer("Готовлю рецепт...")

    try:
        meal = await meal_service.get_by_id(meal_id)
    except ServiceUnavailable:
        await callback.message.answer(
            "😔 Сервис рецептов временно недоступен. Попробуйте ещё раз.",
            reply_markup=result_kb(meal_id),
        )
        return
    if meal is None:
        await callback.message.answer("Рецепт не найден.", reply_markup=play_kb("🔄 Следующий бой"))
        return

    calories = await nutrition_service.get_calories(meal.id, meal.name)

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass

    if meal.image_url:
        try:
            await callback.message.answer_photo(meal.image_url)
        except TelegramBadRequest:
            logger.warning("Could not send recipe photo")

    await callback.message.answer(build_header(meal, calories))

    if meal.instructions:
        chunks = split_text(meal.instructions)
        for i, chunk in enumerate(chunks):
            text = "<b>Приготовление</b>\n" if i == 0 else ""
            text += html.escape(chunk)
            markup = play_kb("🔄 Следующий бой") if i == len(chunks) - 1 else None
            await callback.message.answer(text, reply_markup=markup)
    else:
        await callback.message.answer("Шаги приготовления не указаны.", reply_markup=play_kb("🔄 Следующий бой"))
