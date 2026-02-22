"""FastAPI application for admin SPA and API."""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from urllib.parse import urlparse

import aiosqlite
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from api.bootstrap import ensure_bootstrap_admin
from api.config import settings
from api.routers import applications, auth, campaigns, stats, users
from database.db import DB_PATH, init_db
from migrations.runner import migrate_to_latest

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )
        return response


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

    app.add_middleware(SecurityHeadersMiddleware)

    cors_origins = _sanitize_cors_origins(settings.cors_origins)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

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

    @app.get("/", include_in_schema=False)
    async def root(camp: int | None = None) -> Response:
        site_base = settings.site_base_url.rstrip("/")
        if camp is not None:
            return RedirectResponse(url=f"{site_base}/camp/{camp}", status_code=301)
        return RedirectResponse(url=f"{site_base}/", status_code=307)

    @app.get("/camp/{camp_id}", include_in_schema=False)
    async def campaign_slug(camp_id: int) -> Response:
        site_base = settings.site_base_url.rstrip("/")
        return RedirectResponse(url=f"{site_base}/camp/{camp_id}", status_code=307)

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
