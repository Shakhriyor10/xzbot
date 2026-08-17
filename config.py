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
    OWNER_IDS = {
        int(x.strip())
        for x in _required_env("OWNER_ID").split(",")
        if x.strip()
    }
except ValueError as exc:
    raise RuntimeError("OWNER_ID must contain valid integer IDs") from exc

if not OWNER_IDS:
    raise RuntimeError("OWNER_ID must contain at least one ID")

# Asosiy owner ID — eski kodlar bilan moslik uchun
OWNER_ID = min(OWNER_IDS)

DB_NAME = os.getenv("DB_NAME", "bot_database.db").strip() or "bot_database.db"

TELEGRAM_API_ID_RAW = os.getenv("TELEGRAM_API_ID", "").strip()
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "").strip()
try:
    TELEGRAM_API_ID = int(TELEGRAM_API_ID_RAW) if TELEGRAM_API_ID_RAW else None
except ValueError as exc:
    raise RuntimeError("TELEGRAM_API_ID must be an integer") from exc
ACCOUNT_SESSION_DIR = os.getenv("ACCOUNT_SESSION_DIR", "account_sessions").strip() or "account_sessions"
