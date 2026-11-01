import logging
from datetime import date, timedelta
from urllib.parse import quote

import httpx

from bot.config import WIKI_USER_AGENT
from bot.services.meals import ServiceUnavailable
from bot.utils.cache import MemoryCache
from bot.utils.retry import RetryableError, with_retry

logger = logging.getLogger(__name__)

BASE_URL = (
    "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
    "en.wikipedia/all-access/user"
)


class PopularityService:
    """Популярность блюда = просмотры его статьи в Википедии за последний год."""

    def __init__(self, user_agent: str):
        self._client = httpx.AsyncClient(
            timeout=10, headers={"User-Agent": user_agent}
        )
        self._cache = MemoryCache(maxsize=1024, ttl=24 * 3600)  # сутки

    async def close(self) -> None:
        await self._client.aclose()

    @with_retry
    async def _fetch(self, url: str) -> dict | None:
        response = await self._client.get(url)
        if response.status_code == 404:
            return None  # статьи нет или по ней нет данных
        if response.status_code == 429 or response.status_code >= 500:
            raise RetryableError(f"HTTP {response.status_code}")
        response.raise_for_status()
        return response.json()

    async def yearly_views(self, wiki_title: str) -> int | None:
        """Сумма просмотров за год. None, если данных по статье нет."""
        cached = self._cache.get(wiki_title)
        if cached is not None:
            return cached

        end = date.today() - timedelta(days=2)  # у API небольшая задержка данных
        start = end - timedelta(days=364)
        title = quote(wiki_title.replace(" ", "_"), safe="")
        url = f"{BASE_URL}/{title}/daily/{start:%Y%m%d}/{end:%Y%m%d}"

        try:
            data = await self._fetch(url)
        except (httpx.HTTPError, RetryableError, ValueError) as exc:
            logger.error("Wikipedia pageviews failed (%s)", type(exc).__name__)
            raise ServiceUnavailable("Сервис популярности недоступен") from exc

        if not data:
            return None
        total = sum(item["views"] for item in data.get("items", []))
        if total <= 0:
            return None
        self._cache.set(wiki_title, total)
        return total


popularity_service = PopularityService(WIKI_USER_AGENT)
