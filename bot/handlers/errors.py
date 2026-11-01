import logging

from aiogram import Router
from aiogram.types import ErrorEvent

router = Router()
logger = logging.getLogger(__name__)


@router.error()
async def on_error(event: ErrorEvent) -> bool:
    # В лог попадает только тип ошибки и traceback, без текста сообщений пользователя
    logger.error("Unhandled error: %s", type(event.exception).__name__, exc_info=event.exception)

    update = event.update
    try:
        if update.callback_query:
            await update.callback_query.answer("Что-то пошло не так. Попробуйте ещё раз.", show_alert=True)
        elif update.message:
            await update.message.answer("😔 Что-то пошло не так. Попробуйте ещё раз чуть позже.")
    except Exception:
        pass
    return True
