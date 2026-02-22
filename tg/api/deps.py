"""FastAPI dependencies for authentication and authorization."""

from __future__ import annotations

from typing import Any

import aiosqlite
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.database import fetchone, get_db
from api.security import TokenError, decode_token

bearer_scheme = HTTPBearer(auto_error=False)


def _normalize_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": int(user["id"]),
        "login": user["login"],
        "name": user["name"],
        "role": user["role"],
        "percent": float(user["percent"]) if user["percent"] is not None else None,
        "is_active": bool(user["is_active"]),
        "created_at": user["created_at"],
    }


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict[str, Any]:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    try:
        payload = decode_token(credentials.credentials, expected_type="access")
        user_id = int(payload["sub"])
    except (TokenError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    user = await fetchone(
        db,
        """
        SELECT id, login, name, role, percent, is_active, created_at
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    )
    if not user or not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is inactive or does not exist.",
        )

    return _normalize_user(user)


def require_roles(*roles: str):
    async def _require(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        if user["role"] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )
        return user

    return _require

