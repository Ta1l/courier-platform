"""Initial admin schema and safe applications extension."""

from __future__ import annotations

import sqlite3

revision = "0001"


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    cursor = conn.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    cursor = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table,),
    )
    return cursor.fetchone() is not None


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
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            login         TEXT    NOT NULL UNIQUE,
            password_hash TEXT    NOT NULL,
            name          TEXT    NOT NULL,
            role          TEXT    NOT NULL CHECK (role IN ('admin', 'investor')),
            percent       REAL,
            is_active     INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
            created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS campaigns (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            investor_id INTEGER NOT NULL,
            name        TEXT    NOT NULL,
            budget      REAL    NOT NULL,
            status      TEXT    NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'paused')),
            created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (investor_id) REFERENCES users(id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS refresh_tokens (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            token_hash  TEXT    NOT NULL UNIQUE,
            expires_at  TEXT    NOT NULL,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
            revoked_at  TEXT,
            ip          TEXT,
            user_agent  TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )

    applications_exists = _table_exists(conn, "applications")
    if applications_exists:
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

    conn.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_campaigns_investor_id ON campaigns(investor_id)"
    )
    if applications_exists:
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_applications_campaign_id ON applications(campaign_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status)"
        )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id)"
    )


def downgrade(conn: sqlite3.Connection) -> None:
    conn.execute("DROP INDEX IF EXISTS idx_refresh_tokens_user_id")
    conn.execute("DROP INDEX IF EXISTS idx_applications_status")
    conn.execute("DROP INDEX IF EXISTS idx_applications_campaign_id")
    conn.execute("DROP INDEX IF EXISTS idx_campaigns_investor_id")
    conn.execute("DROP INDEX IF EXISTS idx_users_role")

    if _table_exists(conn, "applications"):
        _rebuild_applications_without_admin_columns(conn)

    conn.execute("DROP TABLE IF EXISTS refresh_tokens")
    conn.execute("DROP TABLE IF EXISTS campaigns")
    conn.execute("DROP TABLE IF EXISTS users")
