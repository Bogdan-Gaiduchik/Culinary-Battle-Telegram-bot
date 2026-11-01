import random
from dataclasses import dataclass

from bot.services.dish_pool import DISH_POOL
from bot.services.meals import Meal, ServiceUnavailable, meal_service
from bot.services.popularity import popularity_service


@dataclass
class BattleDish:
    name: str
    meal: Meal
    views: int


@dataclass
class Battle:
    a: BattleDish
    b: BattleDish

    @property
    def winner(self) -> BattleDish:
        return self.a if self.a.views >= self.b.views else self.b


async def build_battle() -> Battle:
    """Берёт два случайных блюда с данными и рецептом, не слишком близких по популярности."""
    ready: list[BattleDish] = []

    for dish in random.sample(DISH_POOL, len(DISH_POOL)):
        views = await popularity_service.yearly_views(dish.wiki)
        if views is None:
            continue
        # слишком близкие по популярности блюда дают угадывание «на монетке»
        if ready and max(views, ready[0].views) / min(views, ready[0].views) < 1.2:
            continue
        meals = await meal_service.search(dish.query)
        if not meals:
            continue
        ready.append(BattleDish(dish.name, meals[0], views))
        if len(ready) == 2:
            return Battle(ready[0], ready[1])

    raise ServiceUnavailable("Не удалось собрать пару блюд")
