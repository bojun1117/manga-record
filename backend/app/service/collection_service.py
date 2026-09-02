from datetime import datetime, timezone
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AlreadyInCollectionError, ForbiddenError, NotFoundError
from app.model import Manga, MangaCategory, MemberManga, ReadingStatus
from app.repository import manga_repository, member_manga_repository


def search_manga(db: Session, query: str) -> list[Manga]:
    return manga_repository.search_by_title(db, query)


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


def list_collections(db: Session, member_id: int) -> list[tuple[MemberManga, Manga]]:
    return member_manga_repository.list_by_member(db, member_id)


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
