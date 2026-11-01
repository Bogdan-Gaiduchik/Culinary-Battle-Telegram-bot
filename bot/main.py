import asyncio
import logging
from logging.handlers import RotatingFileHandler

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError
from aiogram.types import BotCommand

from bot.config import BOT_TOKEN
from bot.db.session import init_db
from bot.handlers import get_routers
from bot.services.meals import meal_service
from bot.services.nutrition import nutrition_service
from bot.services.popularity import popularity_service
from bot.texts import DESCRIPTION, SHORT_DESCRIPTION

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    console = logging.StreamHandler()
    console.setFormatter(fmt)
    file = RotatingFileHandler(
        "bot.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    file.setFormatter(fmt)
    logging.basicConfig(level=logging.INFO, handlers=[console, file])
    logging.getLogger("httpx").setLevel(logging.WARNING)


async def setup_bot_profile(bot: Bot) -> None:
    """Меню команд и описание бота. Сбой здесь не должен мешать запуску."""
    try:
        await bot.set_my_commands(
            [
                BotCommand(command="play", description="⚔️ Начать бой"),
                BotCommand(command="newbattle", description="👥 Бой для друзей"),
                BotCommand(command="profile", description="👤 Мой профиль"),
                BotCommand(command="top", description="🏆 Топ-10 игроков"),
                BotCommand(command="settings", description="⚙️ Настройки"),
                BotCommand(command="info", description="📖 Инструкция"),
            ]
        )
        await bot.set_my_short_description(short_description=SHORT_DESCRIPTION)
        await bot.set_my_description(description=DESCRIPTION)
    except TelegramAPIError as exc:
        logger.warning("Could not set bot profile: %s", type(exc).__name__)


async def main():
    setup_logging()
    await init_db()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    await setup_bot_profile(bot)

    dp = Dispatcher()
    for router in get_routers():
        dp.include_router(router)

    try:
        await dp.start_polling(bot)
    finally:
        await meal_service.close()
        await popularity_service.close()
        await nutrition_service.close()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен")
