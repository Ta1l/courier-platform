from __future__ import annotations

import sqlite3
import sys
from pathlib import Path


def _load_migrator():
    tg_dir = Path(__file__).resolve().parents[1]
    tg_dir_str = str(tg_dir)
    if tg_dir_str not in sys.path:
        sys.path.insert(0, tg_dir_str)

    for module_name in list(sys.modules):
        if module_name.startswith("migrations."):
            sys.modules.pop(module_name, None)

    from migrations.runner import migrate_to_latest

    return migrate_to_latest


def _application_columns(conn: sqlite3.Connection) -> set[str]:
    cursor = conn.execute("PRAGMA table_info(applications)")
    return {row[1] for row in cursor.fetchall()}


def _create_legacy_applications_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE applications (
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


def test_migration_creates_applications_with_admin_columns_on_empty_db(tmp_path: Path) -> None:
    db_path = tmp_path / "applications.db"
    migrate_to_latest = _load_migrator()

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        applied = migrate_to_latest(conn)
        assert "0001" in applied
        assert "0002" in applied
        assert "0003" in applied

        columns = _application_columns(conn)
        assert "campaign_id" in columns
        assert "revenue" in columns
        assert "status" in columns
    finally:
        conn.close()


def test_migration_repairs_schema_when_0001_applied_before_table_creation(tmp_path: Path) -> None:
    db_path = tmp_path / "applications.db"
    migrate_to_latest = _load_migrator()

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        conn.execute(
            """
            CREATE TABLE schema_migrations (
                revision TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "INSERT INTO schema_migrations (revision, applied_at) VALUES (?, datetime('now'))",
            ("0001",),
        )

        conn.execute(
            """
            CREATE TABLE campaigns (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                investor_id INTEGER NOT NULL,
                name        TEXT    NOT NULL,
                budget      REAL    NOT NULL,
                status      TEXT    NOT NULL DEFAULT 'active',
                created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.execute(
            """
            INSERT INTO campaigns (id, investor_id, name, budget, status, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
            """,
            (7, 1, "Campaign Seven", 1000.0, "active"),
        )

        _create_legacy_applications_table(conn)
        conn.execute(
            """
            INSERT INTO applications (
                telegram_id, username, first_name, phone, age, citizenship, source,
                contacted, submitted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """,
            (111111, "legacy_user", "Legacy User", "+70000000000", 30, "RU", "camp_7", 0),
        )
        conn.commit()

        applied = migrate_to_latest(conn)
        assert applied == ["0002", "0003"]

        columns = _application_columns(conn)
        assert "campaign_id" in columns
        assert "revenue" in columns
        assert "status" in columns

        row = conn.execute(
            "SELECT campaign_id, status FROM applications WHERE telegram_id = ?",
            (111111,),
        ).fetchone()
        assert row == (7, "new")
    finally:
        conn.close()
