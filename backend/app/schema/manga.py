from datetime import datetime

from pydantic import Field, field_validator

from app.model import MangaCategory
from app.schema.base import CamelModel


class MangaSearchResult(CamelModel):
    id: int
    title: str
    category: MangaCategory


class UpdateMangaRequest(CamelModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    category: MangaCategory | None = None

    @field_validator("title")
    @classmethod
    def trim_title(cls, v: str | None) -> str | None:
        if v is None:
            return v
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("title must not be blank")
        return trimmed


class MangaAdminResponse(CamelModel):
    id: int
    title: str
    category: MangaCategory
    created_at: datetime
    updated_at: datetime


class MangaListResponse(CamelModel):
    items: list[MangaSearchResult]
    page: int
    page_size: int
    total: int
