"""API configuration loaded from .env files."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

REPO_DIR = Path(__file__).resolve().parents[2]
TG_DIR = Path(__file__).resolve().parents[1]

load_dotenv(REPO_DIR / ".env")
load_dotenv(TG_DIR / ".env")


def _as_bool(value: str, default: bool = False) -> bool:
    raw = (value or "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name, "").strip()
    if not value:
        return default
    return int(value)


def _parse_cors_origins(raw: str) -> list[str]:
    origins = [item.strip() for item in raw.split(",") if item.strip()]
    return origins or ["http://localhost:5173", "http://127.0.0.1:5173"]


@dataclass(frozen=True)
class Settings:
    api_host: str
    api_port: int
    api_reload: bool
    api_prefix: str
    app_name: str
    cors_origins: list[str]
    jwt_secret: str
    jwt_algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int
    login_rate_limit: int
    login_rate_window_seconds: int
    admin_dist_dir: Path
    site_base_url: str
    bootstrap_admin_login: str
    bootstrap_admin_password: str
    bootstrap_admin_name: str
    auto_migrate: bool


def _resolve_admin_dist_dir(raw_value: str) -> Path:
    raw_path = Path(raw_value).expanduser()
    if raw_path.is_absolute():
        return raw_path
    return (REPO_DIR / raw_path).resolve()


def _build_settings() -> Settings:
    admin_dist_raw = os.getenv("ADMIN_DIST_DIR", "admin-dist").strip() or "admin-dist"
    return Settings(
        api_host=os.getenv("API_HOST", "0.0.0.0").strip() or "0.0.0.0",
        api_port=_int_env("API_PORT", 8000),
        api_reload=_as_bool(os.getenv("API_RELOAD", ""), default=False),
        api_prefix="/api",
        app_name=os.getenv("API_APP_NAME", "Courier Admin API").strip()
        or "Courier Admin API",
        cors_origins=_parse_cors_origins(
            os.getenv(
                "API_CORS_ORIGINS",
                "http://localhost:5173,http://127.0.0.1:5173",
            )
        ),
        jwt_secret=os.getenv("API_JWT_SECRET", "change-me").strip() or "change-me",
        jwt_algorithm=os.getenv("API_JWT_ALGORITHM", "HS256").strip() or "HS256",
        access_token_expire_minutes=_int_env("API_ACCESS_TOKEN_EXPIRE_MINUTES", 15),
        refresh_token_expire_days=_int_env("API_REFRESH_TOKEN_EXPIRE_DAYS", 30),
        login_rate_limit=_int_env("API_LOGIN_RATE_LIMIT", 5),
        login_rate_window_seconds=_int_env("API_LOGIN_RATE_WINDOW_SECONDS", 900),
        admin_dist_dir=_resolve_admin_dist_dir(admin_dist_raw),
        site_base_url=os.getenv("SITE_BASE_URL", "https://kurer-spb.ru").strip()
        or "https://kurer-spb.ru",
        bootstrap_admin_login=os.getenv("ADMIN_BOOTSTRAP_LOGIN", "").strip(),
        bootstrap_admin_password=os.getenv("ADMIN_BOOTSTRAP_PASSWORD", "").strip(),
        bootstrap_admin_name=os.getenv("ADMIN_BOOTSTRAP_NAME", "Administrator").strip()
        or "Administrator",
        auto_migrate=_as_bool(os.getenv("API_AUTO_MIGRATE", "true"), default=True),
    )


settings = _build_settings()
