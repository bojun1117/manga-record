from sqlalchemy import select
from sqlalchemy.orm import Session

from app.model import Manga, MemberManga


def list_by_member(db: Session, member_id: int) -> list[tuple[MemberManga, Manga]]:
    stmt = (
        select(MemberManga, Manga)
        .join(Manga, MemberManga.manga_id == Manga.id)
        .where(MemberManga.member_id == member_id)
    )
    return list(db.execute(stmt).all())


def get_with_manga(db: Session, entry_id: int) -> tuple[MemberManga, Manga] | None:
    stmt = (
        select(MemberManga, Manga)
        .join(Manga, MemberManga.manga_id == Manga.id)
        .where(MemberManga.id == entry_id)
    )
    return db.execute(stmt).first()
