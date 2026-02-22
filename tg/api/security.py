"""Security helpers: bcrypt hashing and JWT tokens."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

from api.config import settings


class TokenError(Exception):
    """Raised when token is invalid or expired."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _to_timestamp(value: datetime) -> int:
    return int(value.timestamp())


def hash_password(password: str) -> str:
    encoded = password.encode("utf-8")
    return bcrypt.hashpw(encoded, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    if not password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def _create_token(
    *,
    user_id: int,
    role: str,
    token_type: str,
    expires_delta: timedelta,
) -> tuple[str, dict[str, Any]]:
    now = _utc_now()
    expires_at = now + expires_delta
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "type": token_type,
        "jti": secrets.token_urlsafe(24),
        "iat": _to_timestamp(now),
        "exp": _to_timestamp(expires_at),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, payload


def create_access_token(user_id: int, role: str) -> tuple[str, dict[str, Any]]:
    return _create_token(
        user_id=user_id,
        role=role,
        token_type="access",
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(user_id: int, role: str) -> tuple[str, dict[str, Any]]:
    return _create_token(
        user_id=user_id,
        role=role,
        token_type="refresh",
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str, *, expected_type: str | None = None) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "sub", "type"]},
        )
    except ExpiredSignatureError as exc:
        raise TokenError("Token has expired.") from exc
    except InvalidTokenError as exc:
        raise TokenError("Invalid token.") from exc

    token_type = payload.get("type")
    if expected_type and token_type != expected_type:
        raise TokenError("Invalid token type.")

    return payload


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

