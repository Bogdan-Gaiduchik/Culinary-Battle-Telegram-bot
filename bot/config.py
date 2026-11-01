import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не задан. Проверьте файл .env")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./bot.db")
THEMEALDB_API_KEY = os.getenv("THEMEALDB_API_KEY", "1")
WIKI_USER_AGENT = os.getenv(
    "WIKI_USER_AGENT",
    "CulinaryBattleBot/1.0 (student project; gaiduchikbogdan2011@gmail.com)",
)
SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY", "")
