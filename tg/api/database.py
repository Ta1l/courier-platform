"""Async database helpers for the admin API."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from typing import Any

import aiosqlite

from database.db import DB_PATH


@asynccontextmanager
async def db_session() -> AsyncIterator[aiosqlite.Connection]:
    conn = await aiosqlite.connect(str(DB_PATH))
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        await conn.close()


async def get_db() -> AsyncIterator[aiosqlite.Connection]:
    async with db_session() as conn:
        yield conn


async def fetchone(
    conn: aiosqlite.Connection,
    query: str,
    params: Sequence[Any] = (),
) -> dict[str, Any] | None:
    cursor = await conn.execute(query, params)
    row = await cursor.fetchone()
    return dict(row) if row else None


async def fetchall(
    conn: aiosqlite.Connection,
    query: str,
    params: Sequence[Any] = (),
) -> list[dict[str, Any]]:
    cursor = await conn.execute(query, params)
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]

