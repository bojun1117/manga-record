from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.search import like_pattern
from app.model import Manga, MangaCategory, MemberManga, ReadingStatus


def _filtered_query(
    member_id: int,
    statuses: list[ReadingStatus] | None,
    category: MangaCategory | None,
    normalized_query: str | None,
):
    conditions = [MemberManga.member_id == member_id]
    if statuses is not None:
        conditions.append(MemberManga.status.in_(statuses))
    if category is not None:
        conditions.append(Manga.category == category)
    if normalized_query:
        conditions.append(Manga.normalized_title.ilike(like_pattern(normalized_query), escape="\\"))
    return conditions


def list_filtered(
    db: Session,
    member_id: int,
    statuses: list[ReadingStatus] | None,
    category: MangaCategory | None,
    normalized_query: str | None,
    offset: int,
    limit: int,
) -> list[tuple[MemberManga, Manga]]:
    conditions = _filtered_query(member_id, statuses, category, normalized_query)
    stmt = (
        select(MemberManga, Manga)
        .join(Manga, MemberManga.manga_id == Manga.id)
        .where(*conditions)
        .order_by(MemberManga.last_read_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(db.execute(stmt).all())


def count_filtered(
    db: Session,
    member_id: int,
    statuses: list[ReadingStatus] | None,
    category: MangaCategory | None,
    normalized_query: str | None,
) -> int:
    conditions = _filtered_query(member_id, statuses, category, normalized_query)
    stmt = (
        select(func.count())
        .select_from(MemberManga)
        .join(Manga, MemberManga.manga_id == Manga.id)
        .where(*conditions)
    )
    return db.scalar(stmt) or 0


def count_by_status(db: Session, member_id: int) -> dict[ReadingStatus, int]:
    stmt = (
        select(MemberManga.status, func.count())
        .where(MemberManga.member_id == member_id)
        .group_by(MemberManga.status)
    )
    return dict(db.execute(stmt).all())


def get_with_manga(db: Session, entry_id: int) -> tuple[MemberManga, Manga] | None:
    stmt = (
        select(MemberManga, Manga)
        .join(Manga, MemberManga.manga_id == Manga.id)
        .where(MemberManga.id == entry_id)
    )
    return db.execute(stmt).first()
