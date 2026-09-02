from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.core.chinese import normalize_chinese, to_traditional
from app.core.search import like_pattern
from app.model import Manga, MangaCategory


def get_by_id(db: Session, manga_id: int) -> Manga | None:
    return db.get(Manga, manga_id)


def list_paginated(db: Session, offset: int, limit: int) -> list[Manga]:
    stmt = select(Manga).order_by(Manga.created_at.desc()).offset(offset).limit(limit)
    return list(db.scalars(stmt))


def count_all(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(Manga)) or 0


def search_by_title(db: Session, query: str, limit: int = 20) -> list[Manga]:
    pattern = like_pattern(normalize_chinese(query))
    stmt = (
        select(Manga)
        .where(Manga.normalized_title.ilike(pattern, escape="\\"))
        .order_by(Manga.title)
        .limit(limit)
    )
    return list(db.scalars(stmt))


def get_or_create(db: Session, title: str, category: MangaCategory) -> Manga:
    normalized = normalize_chinese(title)
    stmt = (
        pg_insert(Manga)
        .values(title=to_traditional(title), normalized_title=normalized, category=category)
        .on_conflict_do_update(
            index_elements=[Manga.normalized_title],
            set_={"updated_at": func.now()},
        )
        .returning(Manga.id)
    )
    manga_id = db.execute(stmt).scalar_one()
    db.flush()
    manga = db.get(Manga, manga_id)
    assert manga is not None
    return manga
