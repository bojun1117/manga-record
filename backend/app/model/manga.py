import enum
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.model.base import Base


class MangaCategory(str, enum.Enum):
    """DATA_MODEL.md 的九個分類。"""

    HOT_BLOODED = "hot_blooded"
    MYSTERY = "mystery"
    ADVENTURE = "adventure"
    ROMANCE = "romance"
    CASUAL = "casual"
    COMPETITION = "competition"
    REVENGE = "revenge"
    SLICE_OF_LIFE = "slice_of_life"
    OTHER = "other"


class Manga(Base):
    """DATA_MODEL.md `manga`。全站共用目錄，沒有 member_id。

    normalized_title 是 UNIQUE：POST /collections 的 get-or-create 靠這個欄位判斷
    「這部漫畫是不是已經有人建過了」，見 API.md §9。
    """

    __tablename__ = "manga"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    normalized_title: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    category: Mapped[MangaCategory] = mapped_column(
        Enum(MangaCategory, name="manga_category", native_enum=True, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=MangaCategory.OTHER,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
