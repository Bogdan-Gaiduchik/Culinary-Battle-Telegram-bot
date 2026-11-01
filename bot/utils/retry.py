import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


class RetryableError(Exception):
    """Временная ошибка сервиса (429, 5xx): имеет смысл повторить запрос."""


def with_retry(func):
    """3 попытки с нарастающей паузой при сетевых сбоях, таймаутах, 429 и 5xx."""
    return retry(
        retry=retry_if_exception_type((httpx.TransportError, RetryableError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
        reraise=True,
    )(func)
