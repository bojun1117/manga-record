from datetime import datetime

from pydantic import Field, field_validator

from app.model import MangaCategory, ReadingStatus
from app.schema.base import CamelModel


class CreateCollectionRequest(CamelModel):
    manga_name: str = Field(min_length=1, max_length=200)
    category: MangaCategory | None = None
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


class CollectionListResponse(CamelModel):
    items: list[CollectionItemResponse]
    page: int
    page_size: int
    total: int


class CollectionStatsResponse(CamelModel):
    total: int
    plan_to_read: int
    reading: int
    completed: int
    dropped: int
