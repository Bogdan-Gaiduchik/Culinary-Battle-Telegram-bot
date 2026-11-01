from aiogram import Router

from bot.handlers import (
    errors,
    friends,
    game,
    info,
    profile,
    recipe,
    settings,
    start,
)


def get_routers() -> list[Router]:
    return [
        errors.router,
        start.router,
        info.router,
        game.router,
        recipe.router,
        profile.router,
        settings.router,
        friends.router,
    ]
