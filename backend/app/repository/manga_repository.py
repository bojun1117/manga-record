from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.core.chinese import normalize_chinese
from app.model import Manga, MangaCategory

_LIKE_ESCAPE_MAP = str.maketrans({"%": "\\%", "_": "\\_", "\\": "\\\\"})


def _escape_like(s: str) -> str:
    return s.translate(_LIKE_ESCAPE_MAP)


def search_by_title(db: Session, query: str, limit: int = 20) -> list[Manga]:
    normalized_query = normalize_chinese(query)
    pattern = f"%{_escape_like(normalized_query)}%"
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
        .values(title=title, normalized_title=normalized, category=category)
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
