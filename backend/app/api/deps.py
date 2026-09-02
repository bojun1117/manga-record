from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.repository import member_repository


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


def require_admin(
    member_id: Annotated[int, Depends(require_auth)],
    db: Session = Depends(get_db),
) -> int:
    member = member_repository.get_by_id(db, member_id)
    if member is None or not member.is_admin:
        raise ForbiddenError("admin access required")
    return member_id
