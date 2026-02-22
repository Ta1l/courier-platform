"""
SQLite database operations for the bot and admin API.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

import aiosqlite

BASE_DIR = Path(__file__).resolve().parents[1]
LEGACY_DB_PATH = BASE_DIR / "applications.db"
DEFAULT_DB_PATH = BASE_DIR / "data" / "applications.db"

logger = logging.getLogger(__name__)


def _default_db_path() -> Path:
    if LEGACY_DB_PATH.exists():
        return LEGACY_DB_PATH
    return DEFAULT_DB_PATH


DB_PATH = Path(os.getenv("DB_PATH", str(_default_db_path()))).expanduser().resolve()


def _db_path() -> str:
    return str(DB_PATH)


def parse_campaign_id_from_source(source: str | None) -> int | None:
    """
    Parse campaign id from deep-link payload.

    Supported formats:
    - camp_123
    - 123
    """
    if not source:
        return None

    raw = source.strip()
    if not raw:
        return None

    if raw.startswith("camp_"):
        raw = raw.split("_", maxsplit=1)[1]

    if not raw.isdigit():
        return None

    campaign_id = int(raw)
    return campaign_id if campaign_id > 0 else None


async def init_db() -> None:
    """
    Create database directory and initialize base schema if needed.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(_db_path()) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS applications (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id  INTEGER NOT NULL,
                username     TEXT,
                first_name   TEXT,
                phone        TEXT    NOT NULL,
                age          INTEGER NOT NULL,
                citizenship  TEXT    NOT NULL,
                source       TEXT,
                contacted    INTEGER NOT NULL DEFAULT 0,
                submitted_at TEXT    NOT NULL
            )
            """
        )
        await db.commit()


async def _table_columns(db: aiosqlite.Connection, table_name: str) -> set[str]:
    cursor = await db.execute(f"PRAGMA table_info({table_name})")
    rows = await cursor.fetchall()
    return {row[1] for row in rows}


async def save_application(data: dict) -> Optional[int]:
    """
    Save a validated application to the database.

    Supports legacy and migrated schema without breaking old flow.
    """
    async with aiosqlite.connect(_db_path()) as db:
        columns = await _table_columns(db, "applications")

        fields = [
            "telegram_id",
            "username",
            "first_name",
            "phone",
            "age",
            "citizenship",
            "source",
            "contacted",
            "submitted_at",
        ]
        values = [
            ":telegram_id",
            ":username",
            ":first_name",
            ":phone",
            ":age",
            ":citizenship",
            ":source",
            ":contacted",
            ":submitted_at",
        ]

        payload = {
            "telegram_id": data.get("telegram_id"),
            "username": data.get("username"),
            "first_name": data.get("first_name"),
            "phone": data.get("phone"),
            "age": data.get("age"),
            "citizenship": data.get("citizenship"),
            "source": data.get("source"),
            "contacted": 0,
            "submitted_at": data.get("submitted_at"),
        }

        if "campaign_id" in columns:
            fields.append("campaign_id")
            values.append(":campaign_id")
            payload["campaign_id"] = data.get("campaign_id")

        if "status" in columns:
            fields.append("status")
            values.append(":status")
            payload["status"] = data.get("status")

        if "revenue" in columns:
            fields.append("revenue")
            values.append(":revenue")
            payload["revenue"] = data.get("revenue")

        cursor = await db.execute(
            f"""
            INSERT INTO applications ({", ".join(fields)})
            VALUES ({", ".join(values)})
            """,
            payload,
        )
        await db.commit()
        return cursor.lastrowid


async def get_campaign_by_id(campaign_id: int) -> Optional[dict]:
    """
    Retrieve campaign by id if campaigns table exists.
    """
    try:
        async with aiosqlite.connect(_db_path()) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT id, investor_id, name, budget, status, created_at
                FROM campaigns
                WHERE id = ?
                """,
                (campaign_id,),
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    except aiosqlite.Error as exc:
        logger.warning("Campaign lookup failed for id=%s: %s", campaign_id, exc)
        return None


async def get_active_campaign(campaign_id: int) -> Optional[dict]:
    """
    Retrieve active campaign by id.
    """
    campaign = await get_campaign_by_id(campaign_id)
    if not campaign:
        return None
    return campaign if campaign.get("status") == "active" else None


async def count_applications() -> int:
    """
    Return total amount of applications.
    """
    async with aiosqlite.connect(_db_path()) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM applications")
        row = await cursor.fetchone()
        return int(row[0]) if row else 0


async def get_applications_page(limit: int = 20, offset: int = 0) -> list[dict]:
    """
    Retrieve a page of applications ordered by newest first.
    """
    safe_limit = max(1, min(limit, 100))
    safe_offset = max(0, offset)

    async with aiosqlite.connect(_db_path()) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT * FROM applications
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            (safe_limit, safe_offset),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_application_by_id(app_id: int) -> Optional[dict]:
    """
    Retrieve a single application by primary key.
    """
    async with aiosqlite.connect(_db_path()) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM applications WHERE id = ?",
            (app_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_all_applications() -> list[dict]:
    """
    Backward-compatible helper for full list retrieval.
    """
    return await get_applications_page(limit=1000, offset=0)


async def mark_contacted(app_id: int) -> bool:
    """
    Mark application as contacted once.
    """
    async with aiosqlite.connect(_db_path()) as db:
        cursor = await db.execute(
            "UPDATE applications SET contacted = 1 WHERE id = ? AND contacted = 0",
            (app_id,),
        )
        await db.commit()
        return cursor.rowcount > 0

