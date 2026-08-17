import os

from dotenv import load_dotenv

load_dotenv()


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Required environment variable {name} is not set")
    return value


TOKEN = _required_env("BOT_TOKEN")

try:
    OWNER_ID = int(_required_env("OWNER_ID"))
except ValueError as exc:
    raise RuntimeError("OWNER_ID must be an integer") from exc

DB_NAME = os.getenv("DB_NAME", "bot_database.db").strip() or "bot_database.db"

TELEGRAM_API_ID_RAW = os.getenv("TELEGRAM_API_ID", "").strip()
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "").strip()
try:
    TELEGRAM_API_ID = int(TELEGRAM_API_ID_RAW) if TELEGRAM_API_ID_RAW else None
except ValueError as exc:
    raise RuntimeError("TELEGRAM_API_ID must be an integer") from exc
ACCOUNT_SESSION_DIR = os.getenv("ACCOUNT_SESSION_DIR", "account_sessions").strip() or "account_sessions"
