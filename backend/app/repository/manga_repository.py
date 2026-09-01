from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.core.chinese import normalize_chinese
from app.model import Manga, MangaCategory

# ILIKE 的萬用字元 %/_ 如果查詢字串裡本身就有這些字元，要跳脫掉，不然會被當成 pattern 解釋
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
    """API.md §9 的 get-or-create：INSERT ... ON CONFLICT (normalized_title)。

    不在這裡 commit——交易邊界由呼叫端（collection_service.create_collection）控制，
    確保「manga 建立」跟「member_manga 建立」要嘛一起成功、要嘛一起 rollback。
    """
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
    assert manga is not None  # 剛 insert/upsert 完，這筆一定存在
    return manga
