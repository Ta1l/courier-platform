"""Authentication routes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import aiosqlite
from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials

from api.config import settings
from api.database import fetchone, get_db
from api.deps import bearer_scheme, get_current_user
from api.rate_limit import login_rate_limiter
from api.schemas import AuthResponse, LoginRequest, LogoutRequest, RefreshRequest, UserOut
from api.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _normalize_user(user: dict[str, Any]) -> UserOut:
    return UserOut(
        id=int(user["id"]),
        login=user["login"],
        name=user["name"],
        role=user["role"],
        percent=float(user["percent"]) if user["percent"] is not None else None,
        is_active=bool(user["is_active"]),
        created_at=user["created_at"],
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    db: aiosqlite.Connection = Depends(get_db),
) -> AuthResponse:
    client_ip = request.client.host if request.client and request.client.host else "unknown"
    allowed, retry_after = await login_rate_limiter.allow(client_ip)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )

    user = await fetchone(
        db,
        """
        SELECT id, login, password_hash, name, role, percent, is_active, created_at
        FROM users
        WHERE login = ?
        """,
        (payload.login,),
    )
    if not user or not user["is_active"] or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
        )

    await login_rate_limiter.reset(client_ip)

    access_token, access_claims = create_access_token(int(user["id"]), user["role"])
    refresh_token, refresh_claims = create_refresh_token(int(user["id"]), user["role"])
    refresh_expires_at = datetime.fromtimestamp(
        int(refresh_claims["exp"]),
        tz=timezone.utc,
    ).strftime("%Y-%m-%d %H:%M:%S")

    await db.execute(
        """
        INSERT INTO refresh_tokens (
            user_id, token_hash, expires_at, created_at, revoked_at, ip, user_agent
        )
        VALUES (?, ?, ?, datetime('now'), NULL, ?, ?)
        """,
        (
            int(user["id"]),
            hash_token(refresh_token),
            refresh_expires_at,
            client_ip,
            request.headers.get("user-agent", "")[:255],
        ),
    )
    await db.commit()

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=max(1, int(access_claims["exp"]) - int(access_claims["iat"])),
        user=_normalize_user(user),
    )


@router.post("/refresh", response_model=AuthResponse)
async def refresh_tokens(
    payload: RefreshRequest,
    request: Request,
    db: aiosqlite.Connection = Depends(get_db),
) -> AuthResponse:
    try:
        claims = decode_token(payload.refresh_token, expected_type="refresh")
        user_id = int(claims["sub"])
    except (TokenError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    token_hash = hash_token(payload.refresh_token)
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    token_row = await fetchone(
        db,
        """
        SELECT
            rt.id AS token_id,
            rt.user_id,
            rt.expires_at,
            rt.revoked_at,
            u.id,
            u.login,
            u.name,
            u.role,
            u.percent,
            u.is_active,
            u.created_at
        FROM refresh_tokens rt
        JOIN users u ON u.id = rt.user_id
        WHERE rt.token_hash = ?
        """,
        (token_hash,),
    )
    if (
        not token_row
        or int(token_row["user_id"]) != user_id
        or token_row["revoked_at"] is not None
        or str(token_row["expires_at"]) < now_utc
        or not token_row["is_active"]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is invalid or expired.",
        )

    # Rotate refresh token to reduce replay risk.
    await db.execute(
        "UPDATE refresh_tokens SET revoked_at = ? WHERE token_hash = ? AND revoked_at IS NULL",
        (now_utc, token_hash),
    )

    access_token, access_claims = create_access_token(user_id, token_row["role"])
    refresh_token, refresh_claims = create_refresh_token(user_id, token_row["role"])
    refresh_expires_at = datetime.fromtimestamp(
        int(refresh_claims["exp"]),
        tz=timezone.utc,
    ).strftime("%Y-%m-%d %H:%M:%S")

    client_ip = request.client.host if request.client and request.client.host else "unknown"
    await db.execute(
        """
        INSERT INTO refresh_tokens (
            user_id, token_hash, expires_at, created_at, revoked_at, ip, user_agent
        )
        VALUES (?, ?, ?, datetime('now'), NULL, ?, ?)
        """,
        (
            user_id,
            hash_token(refresh_token),
            refresh_expires_at,
            client_ip,
            request.headers.get("user-agent", "")[:255],
        ),
    )
    await db.commit()

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=max(1, int(access_claims["exp"]) - int(access_claims["iat"])),
        user=_normalize_user(token_row),
    )


@router.post("/logout")
async def logout(
    payload: LogoutRequest | None = Body(default=None),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict[str, Any]:
    revoked = 0
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    if payload and payload.refresh_token:
        token_hash = hash_token(payload.refresh_token)
        cursor = await db.execute(
            """
            UPDATE refresh_tokens
            SET revoked_at = ?
            WHERE token_hash = ? AND revoked_at IS NULL
            """,
            (now_utc, token_hash),
        )
        revoked += cursor.rowcount

    if credentials and credentials.scheme.lower() == "bearer":
        try:
            claims = decode_token(credentials.credentials, expected_type="access")
            user_id = int(claims["sub"])
            cursor = await db.execute(
                """
                UPDATE refresh_tokens
                SET revoked_at = ?
                WHERE user_id = ? AND revoked_at IS NULL
                """,
                (now_utc, user_id),
            )
            revoked += cursor.rowcount
        except (TokenError, ValueError):
            pass

    await db.commit()
    return {"success": True, "revoked": revoked}


@router.get("/me", response_model=UserOut)
async def me(user: dict[str, Any] = Depends(get_current_user)) -> UserOut:
    return _normalize_user(user)

