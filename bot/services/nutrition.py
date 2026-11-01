import logging

import httpx

from bot.config import SPOONACULAR_API_KEY
from bot.db.cache_repo import get_cache, set_cache
from bot.db.session import async_session
from bot.utils.retry import RetryableError, with_retry

logger = logging.getLogger(__name__)

URL = "https://api.spoonacular.com/recipes/guessNutrition"
CACHE_TTL = 30 * 24 * 3600  # калории блюда не меняются


class NutritionService:
    def __init__(self, api_key: str):
        self._api_key = api_key
        # Ключ передаём в заголовке, а не в URL, чтобы он не попал в логи
        headers = {"x-api-key": api_key} if api_key else {}
        self._client = httpx.AsyncClient(timeout=10, headers=headers)

    async def close(self) -> None:
        await self._client.aclose()

    @with_retry
    async def _fetch(self, title: str) -> dict:
        response = await self._client.get(URL, params={"title": title})
        if response.status_code == 429 or response.status_code >= 500:
            raise RetryableError(f"HTTP {response.status_code}")
        response.raise_for_status()
        return response.json()

    async def get_calories(self, meal_id: str, title: str) -> int | None:
        """Ккал на порцию (оценка). None, если сервис недоступен или лимит исчерпан."""
        if not self._api_key:
            return None

        key = f"calories:{meal_id}"
        async with async_session() as session:
            cached = await get_cache(session, key)
        if cached is not None:
            return int(cached)

        try:
            logger.info("Spoonacular request for meal %s", meal_id)
            data = await self._fetch(title)
            calories = int(round(data["calories"]["value"]))
        except httpx.HTTPStatusError as exc:
            # 401 неверный ключ, 402 исчерпан дневной лимит
            logger.error("Spoonacular HTTP %s", exc.response.status_code)
            return None
        except (httpx.HTTPError, RetryableError, ValueError, KeyError, TypeError) as exc:
            logger.error("Spoonacular failed (%s)", type(exc).__name__)
            return None

        async with async_session() as session:
            await set_cache(session, key, str(calories), CACHE_TTL)
        return calories


nutrition_service = NutritionService(SPOONACULAR_API_KEY)
