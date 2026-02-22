"""FastAPI application for admin SPA and API."""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from urllib.parse import urlparse

import aiosqlite
from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response

from api.bootstrap import ensure_bootstrap_admin
from api.config import settings
from api.routers import applications, auth, campaigns, stats, users
from database.db import DB_PATH, init_db
from migrations.runner import migrate_to_latest

logger = logging.getLogger(__name__)


SECURITY_HEADERS = {
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "base-uri 'self'; "
        "object-src 'none'; "
        "frame-ancestors 'none'; "
        "script-src 'self' 'unsafe-inline' https://mc.yandex.ru "
        "https://www.googletagmanager.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com data:; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://mc.yandex.ru https://api-metrika.yandex.net; "
        "frame-src 'none'; "
        "form-action 'self'; "
        "upgrade-insecure-requests"
    ),
    "Content-Security-Policy-Report-Only": (
        "default-src 'self'; "
        "base-uri 'self'; "
        "object-src 'none'; "
        "frame-ancestors 'none'; "
        "script-src 'self' 'unsafe-inline' https://mc.yandex.ru "
        "https://www.googletagmanager.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com data:; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://mc.yandex.ru https://api-metrika.yandex.net; "
        "frame-src 'none'; "
        "form-action 'self'; "
        "upgrade-insecure-requests"
    ),
}


def _origin_from_url(url: str) -> str | None:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}"


def _sanitize_cors_origins(origins: list[str]) -> list[str]:
    filtered = [origin for origin in origins if origin != "*"]
    if filtered:
        return filtered

    site_origin = _origin_from_url(settings.site_base_url)
    if site_origin:
        logger.warning(
            "Wildcard CORS origin ignored; falling back to SITE_BASE_URL origin: %s",
            site_origin,
        )
        return [site_origin]

    logger.warning(
        "Wildcard CORS origin ignored; falling back to localhost dev origins."
    )
    return ["http://localhost:5173", "http://127.0.0.1:5173"]


def _safe_admin_asset(asset_path: str) -> Path | None:
    if not asset_path:
        return None

    root = settings.admin_dist_dir.resolve()
    candidate = (root / asset_path).resolve()
    if not str(candidate).startswith(str(root)):
        return None
    if candidate.is_file():
        return candidate
    return None


def _admin_index() -> Path:
    return settings.admin_dist_dir.resolve() / "index.html"


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        docs_url=f"{settings.api_prefix}/docs",
        redoc_url=f"{settings.api_prefix}/redoc",
        openapi_url=f"{settings.api_prefix}/openapi.json",
    )

    cors_origins = _sanitize_cors_origins(settings.cors_origins)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.middleware("http")
    async def security_headers_middleware(
        request: Request, call_next
    ) -> Response:
        response = await call_next(request)

        for header, value in SECURITY_HEADERS.items():
            if header not in response.headers:
                response.headers[header] = value

        if "Strict-Transport-Security" not in response.headers:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return response

    api_router = APIRouter(prefix=settings.api_prefix)
    api_router.include_router(auth.router)
    api_router.include_router(users.router)
    api_router.include_router(campaigns.router)
    api_router.include_router(applications.router)
    api_router.include_router(stats.router)
    app.include_router(api_router)

    @app.on_event("startup")
    async def startup_event() -> None:
        await init_db()

        if settings.auto_migrate:
            conn = sqlite3.connect(str(DB_PATH))
            conn.execute("PRAGMA foreign_keys = ON")
            try:
                applied = migrate_to_latest(conn)
            finally:
                conn.close()

            if applied:
                logger.info("Applied DB migrations: %s", ", ".join(applied))

        async with aiosqlite.connect(str(DB_PATH)) as db:
            db.row_factory = aiosqlite.Row
            await db.execute("PRAGMA foreign_keys = ON")
            created = await ensure_bootstrap_admin(db)
            if created:
                logger.info(
                    "Bootstrap admin user created from env: %s",
                    settings.bootstrap_admin_login,
                )

    @app.get("/healthz", include_in_schema=False)
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/admin", include_in_schema=False)
    async def admin_root() -> Response:
        index_path = _admin_index()
        if not index_path.exists():
            return JSONResponse(
                status_code=404,
                content={
                    "detail": (
                        "admin-dist is missing. Build admin SPA first: "
                        "cd admin-spa && npm run build"
                    )
                },
            )
        return FileResponse(index_path)

    @app.get("/admin/{asset_path:path}", include_in_schema=False)
    async def admin_assets(asset_path: str) -> Response:
        index_path = _admin_index()
        if not index_path.exists():
            return JSONResponse(
                status_code=404,
                content={
                    "detail": (
                        "admin-dist is missing. Build admin SPA first: "
                        "cd admin-spa && npm run build"
                    )
                },
            )

        asset = _safe_admin_asset(asset_path)
        if asset:
            return FileResponse(asset)
        return FileResponse(index_path)

    return app


app = create_app()
