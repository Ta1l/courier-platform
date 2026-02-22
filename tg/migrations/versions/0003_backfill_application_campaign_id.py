"""Backfill campaign_id/status for legacy application rows."""

from __future__ import annotations

import sqlite3

revision = "0003"


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    cursor = conn.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    cursor = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table,),
    )
    return cursor.fetchone() is not None


def upgrade(conn: sqlite3.Connection) -> None:
    if not _table_exists(conn, "applications"):
        return

    if _column_exists(conn, "applications", "status"):
        conn.execute(
            """
            UPDATE applications
            SET status = 'new'
            WHERE status IS NULL OR TRIM(status) = ''
            """
        )

    if not (
        _table_exists(conn, "campaigns")
        and _column_exists(conn, "applications", "campaign_id")
    ):
        return

    conn.execute(
        """
        UPDATE applications
        SET campaign_id = CAST(SUBSTR(source, 6) AS INTEGER)
        WHERE campaign_id IS NULL
          AND source GLOB 'camp_[0-9]*'
          AND CAST(SUBSTR(source, 6) AS INTEGER) > 0
          AND EXISTS (
                SELECT 1
                FROM campaigns c
                WHERE c.id = CAST(SUBSTR(source, 6) AS INTEGER)
          )
        """
    )


def downgrade(conn: sqlite3.Connection) -> None:
    # Data backfill is intentionally not reverted.
    return
