"""User management routes (admin only)."""

from __future__ import annotations

from typing import Any

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, status

from api.database import fetchall, fetchone, get_db
from api.deps import require_roles
from api.schemas import UserCreate, UserOut, UserToggleResponse, UserUpdate
from api.security import hash_password

router = APIRouter(prefix="/users", tags=["users"])


def _serialize_user(user: dict[str, Any]) -> UserOut:
    return UserOut(
        id=int(user["id"]),
        login=user["login"],
        name=user["name"],
        role=user["role"],
        percent=float(user["percent"]) if user["percent"] is not None else None,
        is_active=bool(user["is_active"]),
        created_at=user["created_at"],
    )


async def _get_user_by_id(db: aiosqlite.Connection, user_id: int) -> dict[str, Any] | None:
    return await fetchone(
        db,
        """
        SELECT id, login, name, role, percent, is_active, created_at
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    )


@router.get("", response_model=list[UserOut])
async def list_users(
    _: dict[str, Any] = Depends(require_roles("admin")),
    db: aiosqlite.Connection = Depends(get_db),
) -> list[UserOut]:
    users = await fetchall(
        db,
        """
        SELECT id, login, name, role, percent, is_active, created_at
        FROM users
        ORDER BY id ASC
        """,
    )
    return [_serialize_user(user) for user in users]


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    _: dict[str, Any] = Depends(require_roles("admin")),
    db: aiosqlite.Connection = Depends(get_db),
) -> UserOut:
    percent = payload.percent if payload.role == "investor" else None

    try:
        cursor = await db.execute(
            """
            INSERT INTO users (
                login, password_hash, name, role, percent, is_active, created_at
            )
            VALUES (?, ?, ?, ?, ?, 1, datetime('now'))
            """,
            (
                payload.login,
                hash_password(payload.password),
                payload.name,
                payload.role,
                percent,
            ),
        )
    except aiosqlite.IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this login already exists.",
        ) from exc

    await db.commit()
    user = await _get_user_by_id(db, int(cursor.lastrowid))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load created user.",
        )
    return _serialize_user(user)


@router.put("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    current_admin: dict[str, Any] = Depends(require_roles("admin")),
    db: aiosqlite.Connection = Depends(get_db),
) -> UserOut:
    existing = await fetchone(
        db,
        """
        SELECT id, login, name, role, percent, is_active, created_at
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    )
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    changes = payload.model_dump(exclude_unset=True)
    updates: dict[str, Any] = {}

    if "login" in changes:
        updates["login"] = changes["login"]
    if "name" in changes:
        updates["name"] = changes["name"]
    if "password" in changes and changes["password"]:
        updates["password_hash"] = hash_password(changes["password"])
    if "role" in changes:
        updates["role"] = changes["role"]

    next_role = updates.get("role", existing["role"])
    if next_role == "admin":
        updates["percent"] = None
    elif "percent" in changes:
        updates["percent"] = changes["percent"]
    elif existing["percent"] is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="percent is required for investor role.",
        )

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update.",
        )

    set_clause = ", ".join(f"{field} = ?" for field in updates)
    params = list(updates.values()) + [user_id]

    try:
        await db.execute(f"UPDATE users SET {set_clause} WHERE id = ?", params)
    except aiosqlite.IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Login is already taken.",
        ) from exc

    await db.commit()
    user = await _get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load updated user.",
        )
    return _serialize_user(user)


@router.patch("/{user_id}/toggle", response_model=UserToggleResponse)
async def toggle_user_active(
    user_id: int,
    current_admin: dict[str, Any] = Depends(require_roles("admin")),
    db: aiosqlite.Connection = Depends(get_db),
) -> UserToggleResponse:
    user = await _get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    if int(user["id"]) == int(current_admin["id"]) and bool(user["is_active"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot disable your own active account.",
        )

    next_state = 0 if bool(user["is_active"]) else 1
    await db.execute("UPDATE users SET is_active = ? WHERE id = ?", (next_state, user_id))
    await db.commit()

    updated = await _get_user_by_id(db, user_id)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load updated user.",
        )

    return UserToggleResponse(success=True, user=_serialize_user(updated))

