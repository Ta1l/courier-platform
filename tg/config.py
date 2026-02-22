"""
config.py — Configuration module.
Loads and validates environment variables from .env.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
LEGACY_DB_PATH = BASE_DIR / "applications.db"
DEFAULT_DB_PATH = BASE_DIR / "data" / "applications.db"


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(
            f"Environment variable '{name}' is required. "
            "Create tg/.env from tg/.env.example."
        )
    return value


def _parse_admin_id(value: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError("Environment variable 'ADMIN_ID' must be an integer.") from exc


BOT_TOKEN: str = _require_env("BOT_TOKEN")
ADMIN_ID: int = _parse_admin_id(_require_env("ADMIN_ID"))


def _default_db_path() -> Path:
    if LEGACY_DB_PATH.exists():
        return LEGACY_DB_PATH
    return DEFAULT_DB_PATH


# Can be absolute or relative. Set DB_PATH explicitly to migrate from legacy path.
DB_PATH: Path = Path(
    os.getenv("DB_PATH", str(_default_db_path()))
).expanduser().resolve()
