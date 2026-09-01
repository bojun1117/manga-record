# API.md §3.1 / §9 / §10

from datetime import datetime

from pydantic import Field, field_validator

from app.model import MangaCategory, ReadingStatus
from app.schema.base import CamelModel


class CreateCollectionRequest(CamelModel):
    """POST /collections。沒有 mangaId 欄位——一律靠 mangaName 由後端 get-or-create，見 API.md §9。"""

    manga_name: str = Field(min_length=1, max_length=200)
    category: MangaCategory | None = None  # 只有「真的新建 manga」時才會被採用
    status: ReadingStatus = ReadingStatus.PLAN_TO_READ
    current_volume: int | None = Field(default=None, ge=0, le=9999)
    current_chapter: int | None = Field(default=None, ge=0, le=9999)
    rating: int | None = Field(default=None, ge=1, le=5)

    @field_validator("manga_name")
    @classmethod
    def trim_manga_name(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("mangaName must not be blank")
        return trimmed


class UpdateCollectionRequest(CamelModel):
    """PATCH /collections/{id}。所有欄位都選填，只有 request body 裡真的出現的 key 才會被更新
    （partial update 語意，靠 exclude_unset=True 判斷，見 API.md §1.3）。
    """

    status: ReadingStatus | None = None
    current_volume: int | None = Field(default=None, ge=0, le=9999)
    current_chapter: int | None = Field(default=None, ge=0, le=9999)
    rating: int | None = Field(default=None, ge=1, le=5)


class CollectionItemResponse(CamelModel):
    id: int
    manga_id: int
    title: str
    category: MangaCategory
    status: ReadingStatus
    current_volume: int | None
    current_chapter: int | None
    rating: int | None
    last_read_at: datetime
    created_at: datetime
    updated_at: datetime
