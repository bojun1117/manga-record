# 匯入所有 model，讓 Base.metadata 拿得到完整的表定義（Alembic env.py 靠這個 import 抓 schema）。

from app.model.base import Base
from app.model.manga import Manga, MangaCategory
from app.model.member import Member
from app.model.member_manga import MemberManga, ReadingStatus

__all__ = [
    "Base",
    "Manga",
    "MangaCategory",
    "Member",
    "MemberManga",
    "ReadingStatus",
]
