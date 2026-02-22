"""Ensure applications table has admin columns even on late creation."""

from __future__ import annotations

import sqlite3

revision = "0002"


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    cursor = conn.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    cursor = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table,),
    )
    return cursor.fetchone() is not None


def _create_applications_with_admin_columns(conn: sqlite3.Connection) -> None:
    conn.execute(
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
            submitted_at TEXT    NOT NULL,
            campaign_id  INTEGER REFERENCES campaigns(id),
            revenue      REAL,
            status       TEXT
        )
        """
    )


def _rebuild_applications_without_admin_columns(conn: sqlite3.Connection) -> None:
    required = [
        "id",
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
    existing_columns = {row[1] for row in conn.execute("PRAGMA table_info(applications)")}
    if not all(column in existing_columns for column in required):
        return

    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS applications__rollback (
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
    conn.execute(
        """
        INSERT INTO applications__rollback (
            id, telegram_id, username, first_name, phone, age,
            citizenship, source, contacted, submitted_at
        )
        SELECT
            id, telegram_id, username, first_name, phone, age,
            citizenship, source, contacted, submitted_at
        FROM applications
        """
    )
    conn.execute("DROP TABLE applications")
    conn.execute("ALTER TABLE applications__rollback RENAME TO applications")
    conn.execute("PRAGMA foreign_keys = ON")


def upgrade(conn: sqlite3.Connection) -> None:
    applications_exists = _table_exists(conn, "applications")
    if not applications_exists:
        _create_applications_with_admin_columns(conn)
        applications_exists = True

    if not _column_exists(conn, "applications", "campaign_id"):
        conn.execute(
            """
            ALTER TABLE applications
            ADD COLUMN campaign_id INTEGER REFERENCES campaigns(id)
            """
        )
    if not _column_exists(conn, "applications", "revenue"):
        conn.execute(
            """
            ALTER TABLE applications
            ADD COLUMN revenue REAL
            """
        )
    if not _column_exists(conn, "applications", "status"):
        conn.execute(
            """
            ALTER TABLE applications
            ADD COLUMN status TEXT
            """
        )

    if applications_exists:
        conn.execute(
            """
            UPDATE applications
            SET status = 'new'
            WHERE status IS NULL OR TRIM(status) = ''
            """
        )
        if _table_exists(conn, "campaigns"):
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
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_applications_campaign_id ON applications(campaign_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status)"
        )


def downgrade(conn: sqlite3.Connection) -> None:
    conn.execute("DROP INDEX IF EXISTS idx_applications_status")
    conn.execute("DROP INDEX IF EXISTS idx_applications_campaign_id")
    if _table_exists(conn, "applications"):
        _rebuild_applications_without_admin_columns(conn)
