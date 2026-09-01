from sqlalchemy import select
from sqlalchemy.orm import Session

from app.model import Member


def get_by_username(db: Session, username: str) -> Member | None:
    return db.scalar(select(Member).where(Member.username == username))


def get_by_id(db: Session, member_id: int) -> Member | None:
    return db.get(Member, member_id)
