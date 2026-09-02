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


_SORT_COLUMNS = {
    "rating": MemberManga.rating,
    "last_read_at": MemberManga.last_read_at,
    "current_chapter": MemberManga.current_chapter,
    "created_at": MemberManga.created_at,
}


def list_for_assistant(
    db: Session,
    member_id: int,
    statuses: list[ReadingStatus] | None,
    categories: list[MangaCategory] | None,
    min_rating: int | None,
    max_rating: int | None,
    sort_by: str,
    sort_order: str,
    limit: int,
) -> list[tuple[MemberManga, Manga]]:
    conditions = [MemberManga.member_id == member_id]
    if statuses is not None:
        conditions.append(MemberManga.status.in_(statuses))
    if categories is not None:
        conditions.append(Manga.category.in_(categories))
    if min_rating is not None:
        conditions.append(MemberManga.rating >= min_rating)
    if max_rating is not None:
        conditions.append(MemberManga.rating <= max_rating)

    column = _SORT_COLUMNS[sort_by]
    order = column.desc() if sort_order == "desc" else column.asc()
    if sort_by in ("rating", "current_chapter"):
        order = order.nulls_last()

    stmt = (
        select(MemberManga, Manga)
        .join(Manga, MemberManga.manga_id == Manga.id)
        .where(*conditions)
        .order_by(order)
        .limit(limit)
    )
    return list(db.execute(stmt).all())


def get_with_manga(db: Session, entry_id: int) -> tuple[MemberManga, Manga] | None:
    stmt = (
        select(MemberManga, Manga)
        .join(Manga, MemberManga.manga_id == Manga.id)
        .where(MemberManga.id == entry_id)
    )
    return db.execute(stmt).first()
