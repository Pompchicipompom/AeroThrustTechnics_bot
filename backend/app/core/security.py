from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt
from jwt import InvalidTokenError

from app.core.config import get_settings

_PASSWORD_SCHEME = "pbkdf2_sha256"


@dataclass(slots=True, frozen=True)
class AdminAccessTokenPayload:
    admin_user_id: int
    role: str
    zone: str | None


def hash_password(password: str) -> str:
    settings = get_settings()
    if not password:
        raise ValueError("Password cannot be empty.")

    salt = secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        settings.admin_password_hash_iterations,
    )
    digest = base64.urlsafe_b64encode(derived).decode("ascii")
    return f"{_PASSWORD_SCHEME}${settings.admin_password_hash_iterations}${salt}${digest}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        scheme, iterations_raw, salt, digest = password_hash.split("$", maxsplit=3)
    except ValueError:
        return False

    if scheme != _PASSWORD_SCHEME:
        return False

    try:
        iterations = int(iterations_raw)
    except ValueError:
        return False

    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    )
    expected_digest = base64.urlsafe_b64encode(derived).decode("ascii")
    return hmac.compare_digest(expected_digest, digest)


def create_admin_access_token(
    *,
    admin_user_id: int,
    role: str,
    zone: str | None,
) -> tuple[str, datetime]:
    settings = get_settings()
    now = datetime.now(tz=UTC)
    ttl_minutes = settings.admin_access_token_ttl_minutes
    non_expiring = ttl_minutes <= 0
    expires_at = now + timedelta(days=36500) if non_expiring else now + timedelta(minutes=ttl_minutes)
    payload = {
        "sub": str(admin_user_id),
        "role": role,
        "zone": zone,
        "iat": int(now.timestamp()),
        "type": "access",
    }
    if not non_expiring:
        payload["exp"] = int(expires_at.timestamp())
    token = jwt.encode(
        payload,
        key=settings.admin_jwt_secret,
        algorithm=settings.admin_jwt_algorithm,
    )
    return token, expires_at


def decode_admin_access_token(token: str) -> AdminAccessTokenPayload:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            key=settings.admin_jwt_secret,
            algorithms=[settings.admin_jwt_algorithm],
        )
    except InvalidTokenError as exc:
        raise ValueError("Invalid token.") from exc

    if payload.get("type") != "access":
        raise ValueError("Invalid token type.")

    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject.isdigit():
        raise ValueError("Invalid token subject.")

    role = payload.get("role")
    if not isinstance(role, str) or not role:
        raise ValueError("Invalid token role.")

    zone = payload.get("zone")
    if zone is not None and not isinstance(zone, str):
        raise ValueError("Invalid token zone.")

    return AdminAccessTokenPayload(
        admin_user_id=int(subject),
        role=role,
        zone=zone,
    )
