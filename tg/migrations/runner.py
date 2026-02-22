"""Lightweight migration runner for SQLite."""

from __future__ import annotations

import argparse
import importlib.util
import os
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

TG_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = TG_DIR.parent
VERSIONS_DIR = Path(__file__).resolve().parent / "versions"

if str(TG_DIR) not in sys.path:
    sys.path.insert(0, str(TG_DIR))


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", maxsplit=1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue

        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]

        os.environ.setdefault(key, value)


_load_env_file(REPO_DIR / ".env")
_load_env_file(TG_DIR / ".env")

from database.db import DB_PATH  # noqa: E402

SCHEMA_MIGRATIONS_TABLE = "schema_migrations"


@dataclass(frozen=True)
class Migration:
    revision: str
    module_name: str
    upgrade: Callable[[sqlite3.Connection], None]
    downgrade: Callable[[sqlite3.Connection], None]


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _ensure_migrations_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA_MIGRATIONS_TABLE} (
            revision TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
        """
    )


def _load_migration(path: Path) -> Migration:
    module_name = f"migration_{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if not spec or not spec.loader:
        raise RuntimeError(f"Failed to load migration module from: {path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    revision = getattr(module, "revision", None)
    upgrade = getattr(module, "upgrade", None)
    downgrade = getattr(module, "downgrade", None)

    if not revision or not callable(upgrade) or not callable(downgrade):
        raise RuntimeError(
            f"Migration {path.name} must define revision, upgrade(conn), downgrade(conn)."
        )

    return Migration(
        revision=str(revision),
        module_name=module_name,
        upgrade=upgrade,
        downgrade=downgrade,
    )


def _load_migrations() -> list[Migration]:
    if not VERSIONS_DIR.exists():
        return []

    migration_files = sorted(
        p
        for p in VERSIONS_DIR.iterdir()
        if p.is_file() and p.suffix == ".py" and not p.name.startswith("__")
    )
    return [_load_migration(path) for path in migration_files]


def _get_applied_revisions(conn: sqlite3.Connection) -> list[str]:
    _ensure_migrations_table(conn)
    cursor = conn.execute(
        f"SELECT revision FROM {SCHEMA_MIGRATIONS_TABLE} ORDER BY revision ASC"
    )
    return [row[0] for row in cursor.fetchall()]


def _apply_upgrade(conn: sqlite3.Connection, migration: Migration) -> None:
    with conn:
        migration.upgrade(conn)
        conn.execute(
            f"""
            INSERT INTO {SCHEMA_MIGRATIONS_TABLE} (revision, applied_at)
            VALUES (?, ?)
            """,
            (migration.revision, _utc_now()),
        )


def _apply_downgrade(conn: sqlite3.Connection, migration: Migration) -> None:
    with conn:
        migration.downgrade(conn)
        conn.execute(
            f"DELETE FROM {SCHEMA_MIGRATIONS_TABLE} WHERE revision = ?",
            (migration.revision,),
        )


def migrate_to_latest(conn: sqlite3.Connection) -> list[str]:
    migrations = _load_migrations()
    applied = set(_get_applied_revisions(conn))
    applied_now: list[str] = []

    for migration in migrations:
        if migration.revision in applied:
            continue
        _apply_upgrade(conn, migration)
        applied_now.append(migration.revision)

    return applied_now


def rollback(conn: sqlite3.Connection, steps: int = 1) -> list[str]:
    if steps < 1:
        return []

    migrations = _load_migrations()
    applied_revisions = _get_applied_revisions(conn)
    applied_set = set(applied_revisions)
    applied_migrations = [m for m in migrations if m.revision in applied_set]

    to_rollback = list(reversed(applied_migrations[-steps:]))
    rolled_back: list[str] = []

    for migration in to_rollback:
        _apply_downgrade(conn, migration)
        rolled_back.append(migration.revision)

    return rolled_back


def print_status(conn: sqlite3.Connection) -> None:
    migrations = _load_migrations()
    applied = set(_get_applied_revisions(conn))

    if not migrations:
        print("No migrations found.")
        return

    for migration in migrations:
        status = "applied" if migration.revision in applied else "pending"
        print(f"{migration.revision}: {status}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SQLite migration runner.")
    parser.add_argument(
        "--db",
        type=str,
        default=str(DB_PATH),
        help="Path to sqlite database file.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("upgrade", help="Apply all pending migrations.")

    downgrade_parser = subparsers.add_parser(
        "downgrade", help="Rollback latest migrations."
    )
    downgrade_parser.add_argument(
        "--steps",
        type=int,
        default=1,
        help="How many latest revisions to rollback.",
    )

    subparsers.add_parser("status", help="Show migration status.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    db_path = Path(args.db).expanduser().resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    _ensure_migrations_table(conn)

    try:
        if args.command == "upgrade":
            applied = migrate_to_latest(conn)
            if applied:
                print(f"Applied: {', '.join(applied)}")
            else:
                print("No pending migrations.")
        elif args.command == "downgrade":
            rolled_back = rollback(conn, steps=args.steps)
            if rolled_back:
                print(f"Rolled back: {', '.join(rolled_back)}")
            else:
                print("Nothing to rollback.")
        elif args.command == "status":
            print_status(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
