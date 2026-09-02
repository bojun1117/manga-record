from datetime import datetime, timezone
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.chinese import normalize_chinese, to_traditional
from app.core.errors import (
    AlreadyInCollectionError,
    DuplicateTitleError,
    ForbiddenError,
    NotFoundError,
)
from app.model import Manga, MangaCategory, MemberManga, ReadingStatus
from app.repository import manga_repository, member_manga_repository


def search_manga(db: Session, query: str) -> list[Manga]:
    return manga_repository.search_by_title(db, query)


def list_manga(db: Session, page: int, page_size: int) -> tuple[list[Manga], int]:
    offset = (page - 1) * page_size
    items = manga_repository.list_paginated(db, offset, page_size)
    total = manga_repository.count_all(db)
    return items, total


def update_manga(
    db: Session,
    manga_id: int,
    title: str | None,
    category: MangaCategory | None,
) -> Manga:
    manga = manga_repository.get_by_id(db, manga_id)
    if manga is None:
        raise NotFoundError("manga not found")

    if title is not None:
        manga.title = to_traditional(title)
        manga.normalized_title = normalize_chinese(title)
    if category is not None:
        manga.category = category

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateTitleError("this title is already used by another manga") from exc

    db.refresh(manga)
    return manga


def create_collection(
    db: Session,
    member_id: int,
    manga_name: str,
    category: MangaCategory | None,
    status: ReadingStatus,
    current_volume: int | None,
    current_chapter: int | None,
    rating: int | None,
) -> tuple[MemberManga, Manga]:
    manga = manga_repository.get_or_create(db, manga_name, category or MangaCategory.OTHER)

    entry = MemberManga(
        member_id=member_id,
        manga_id=manga.id,
        status=status,
        current_volume=current_volume,
        current_chapter=current_chapter,
        rating=rating,
    )
    db.add(entry)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise AlreadyInCollectionError("this manga is already in your collection") from exc

    db.refresh(entry)
    db.refresh(manga)
    return entry, manga


def list_collections_page(
    db: Session,
    member_id: int,
    statuses: list[ReadingStatus] | None,
    category: MangaCategory | None,
    query: str | None,
    page: int,
    page_size: int,
) -> tuple[list[tuple[MemberManga, Manga]], int]:
    normalized_query = normalize_chinese(query) if query else None
    offset = (page - 1) * page_size
    items = member_manga_repository.list_filtered(
        db, member_id, statuses, category, normalized_query, offset, page_size
    )
    total = member_manga_repository.count_filtered(db, member_id, statuses, category, normalized_query)
    return items, total


def get_collection_stats(db: Session, member_id: int) -> dict[str, int]:
    counts = member_manga_repository.count_by_status(db, member_id)
    plan_to_read = counts.get(ReadingStatus.PLAN_TO_READ, 0)
    reading = counts.get(ReadingStatus.READING, 0)
    completed = counts.get(ReadingStatus.COMPLETED, 0)
    dropped = counts.get(ReadingStatus.DROPPED, 0)
    return {
        "total": plan_to_read + reading + completed + dropped,
        "plan_to_read": plan_to_read,
        "reading": reading,
        "completed": completed,
        "dropped": dropped,
    }


def _get_owned_entry(db: Session, member_id: int, entry_id: int) -> tuple[MemberManga, Manga]:
    result = member_manga_repository.get_with_manga(db, entry_id)
    if result is None:
        raise NotFoundError("collection entry not found")
    entry, manga = result
    if entry.member_id != member_id:
        raise ForbiddenError("this collection entry does not belong to you")
    return entry, manga


def update_collection(
    db: Session,
    member_id: int,
    entry_id: int,
    fields: dict[str, Any],
) -> tuple[MemberManga, Manga]:
    entry, manga = _get_owned_entry(db, member_id, entry_id)

    touches_progress = "current_volume" in fields or "current_chapter" in fields
    for key, value in fields.items():
        setattr(entry, key, value)
    if touches_progress:
        entry.last_read_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(entry)
    return entry, manga


def delete_collection(db: Session, member_id: int, entry_id: int) -> None:
    entry, _manga = _get_owned_entry(db, member_id, entry_id)
    db.delete(entry)
    db.commit()
