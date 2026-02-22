"""Bootstrap helpers for admin API startup."""

from __future__ import annotations

import aiosqlite

from api.config import settings
from api.database import fetchone
from api.security import hash_password


async def ensure_bootstrap_admin(db: aiosqlite.Connection) -> bool:
    """Create initial admin user from env if it does not exist."""
    if not settings.bootstrap_admin_login or not settings.bootstrap_admin_password:
        return False

    existing = await fetchone(
        db,
        "SELECT id FROM users WHERE login = ?",
        (settings.bootstrap_admin_login,),
    )
    if existing:
        return False

    await db.execute(
        """
        INSERT INTO users (login, password_hash, name, role, percent, is_active, created_at)
        VALUES (?, ?, ?, 'admin', NULL, 1, datetime('now'))
        """,
        (
            settings.bootstrap_admin_login,
            hash_password(settings.bootstrap_admin_password),
            settings.bootstrap_admin_name,
        ),
    )
    await db.commit()
    return True

