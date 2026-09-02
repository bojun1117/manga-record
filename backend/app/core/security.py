from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import get_settings

JWT_ALGORITHM = "HS256"

_BCRYPT_MAX_BYTES = 72


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > _BCRYPT_MAX_BYTES:
        raise ValueError("password exceeds bcrypt's 72-byte limit")
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(subject: str) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(seconds=settings.jwt_ttl_seconds),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> str:
    settings = get_settings()
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[JWT_ALGORITHM])
    return payload["sub"]
