import re

# Буквы любых языков, цифры, пробелы и немного знаков препинания
_DISH_RE = re.compile(r"^[\w\s'’\-\.,&()]+$")


def clean_dish_name(raw: str | None) -> str | None:
    """Возвращает очищенное название блюда или None, если ввод некорректный."""
    if not raw:
        return None
    name = " ".join(raw.split())  # убираем лишние пробелы и переносы
    if not 2 <= len(name) <= 40:
        return None
    if name.startswith("/"):  # команда, а не название
        return None
    if not any(ch.isalpha() for ch in name):
        return None
    if not _DISH_RE.match(name):  # эмодзи, спецсимволы и т.п.
        return None
    return name
