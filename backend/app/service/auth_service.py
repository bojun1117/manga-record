from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import UnauthorizedError, UsernameTakenError
from app.core.security import create_access_token, hash_password, verify_password
from app.model import Member
from app.repository import member_repository


def register(db: Session, username: str, password: str) -> Member:
    if member_repository.get_by_username(db, username) is not None:
        raise UsernameTakenError(f"username '{username}' is already taken")

    member = Member(username=username, password_hash=hash_password(password))
    db.add(member)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise UsernameTakenError(f"username '{username}' is already taken") from exc
    db.refresh(member)
    return member


def login(db: Session, username: str, password: str) -> str:
    member = member_repository.get_by_username(db, username)
    if member is None or not verify_password(password, member.password_hash):
        raise UnauthorizedError("invalid username or password")
    return create_access_token(str(member.id))
