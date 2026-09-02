from typing import Annotated

from fastapi import Depends, Header

from app.core.errors import UnauthorizedError
from app.core.security import decode_access_token


def _extract_bearer_token(authorization: Annotated[str | None, Header()] = None) -> str:
    if not authorization:
        raise UnauthorizedError("missing Authorization header")
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise UnauthorizedError("Authorization header must be 'Bearer <token>'")
    return parts[1]


def require_auth(token: Annotated[str, Depends(_extract_bearer_token)]) -> int:
    try:
        sub = decode_access_token(token)
        return int(sub)
    except UnauthorizedError:
        raise
    except Exception as exc:
        raise UnauthorizedError("invalid or expired token") from exc
