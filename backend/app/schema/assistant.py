from typing import Literal

from pydantic import BaseModel, Field

from app.model import MangaCategory, ReadingStatus
from app.schema.base import CamelModel
from app.schema.collection import CollectionItemResponse


class AssistantQueryPlan(BaseModel):
    answerable: bool
    summary: str
    statuses: list[ReadingStatus] | None = None
    categories: list[MangaCategory] | None = None
    min_rating: int | None = Field(default=None, ge=1, le=5)
    max_rating: int | None = Field(default=None, ge=1, le=5)
    sort_by: Literal["rating", "last_read_at", "current_chapter", "created_at"] = "last_read_at"
    sort_order: Literal["asc", "desc"] = "desc"
    limit: int = Field(default=20, ge=1, le=50)


class AssistantQueryRequest(CamelModel):
    question: str = Field(min_length=1, max_length=500)


class AssistantQueryResponse(CamelModel):
    answer: str
    items: list[CollectionItemResponse]
