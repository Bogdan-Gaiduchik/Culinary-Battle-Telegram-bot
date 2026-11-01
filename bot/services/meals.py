import logging
from dataclasses import dataclass, field

import httpx

from bot.config import THEMEALDB_API_KEY
from bot.utils.cache import MemoryCache
from bot.utils.retry import RetryableError, with_retry

logger = logging.getLogger(__name__)


class ServiceUnavailable(Exception):
    """Внешний сервис недоступен: handler показывает пользователю понятное сообщение."""


@dataclass
class Meal:
    id: str
    name: str
    category: str
    area: str
    instructions: str
    image_url: str
    youtube_url: str | None
    ingredients: list[tuple[str, str]] = field(default_factory=list)  # (название, мера)


def _parse_meal(raw: dict) -> Meal:
    ingredients = []
    for i in range(1, 21):
        name = (raw.get(f"strIngredient{i}") or "").strip()
        measure = (raw.get(f"strMeasure{i}") or "").strip()
        if name:
            ingredients.append((name, measure))

    return Meal(
        id=raw["idMeal"],
        name=raw["strMeal"],
        category=raw.get("strCategory") or "",
        area=raw.get("strArea") or "",
        instructions=(raw.get("strInstructions") or "").strip(),
        image_url=raw.get("strMealThumb") or "",
        youtube_url=(raw.get("strYoutube") or "").strip() or None,
        ingredients=ingredients,
    )


class MealService:
    def __init__(self, api_key: str):
        self._base_url = f"https://www.themealdb.com/api/json/v1/{api_key}"
        self._client = httpx.AsyncClient(timeout=10)
        self._cache = MemoryCache(maxsize=512, ttl=3600)  # 1 час

    async def close(self) -> None:
        await self._client.aclose()

    @with_retry
    async def _request(self, endpoint: str, params: dict) -> dict:
        response = await self._client.get(f"{self._base_url}/{endpoint}", params=params)
        if response.status_code == 429 or response.status_code >= 500:
            raise RetryableError(f"HTTP {response.status_code}")
        response.raise_for_status()
        return response.json()

    async def _get(self, endpoint: str, params: dict, use_cache: bool = True) -> list[dict]:
        cache_key = f"{endpoint}?{sorted(params.items())}"
        if use_cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        try:
            data = await self._request(endpoint, params)
        except (httpx.HTTPError, RetryableError, ValueError) as exc:
            logger.error("TheMealDB request failed: %s (%s)", endpoint, type(exc).__name__)
            raise ServiceUnavailable("TheMealDB недоступен") from exc

        meals = data.get("meals") or []
        if use_cache:
            self._cache.set(cache_key, meals)
        return meals

    async def random_meal(self) -> Meal:
        # Случайные блюда не кэшируем, иначе пользователь будет получать одно и то же
        meals = await self._get("random.php", {}, use_cache=False)
        if not meals:
            raise ServiceUnavailable("Пустой ответ TheMealDB")
        return _parse_meal(meals[0])

    async def search(self, name: str) -> list[Meal]:
        meals = await self._get("search.php", {"s": name})
        return [_parse_meal(m) for m in meals]

    async def get_by_id(self, meal_id: str) -> Meal | None:
        meals = await self._get("lookup.php", {"i": meal_id})
        return _parse_meal(meals[0]) if meals else None


meal_service = MealService(THEMEALDB_API_KEY)