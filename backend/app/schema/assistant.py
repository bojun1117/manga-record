from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.model import MangaCategory, ReadingStatus
from app.schema.base import CamelModel
from app.schema.collection import CollectionItemResponse


class _CollectionFilterArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    statuses: list[ReadingStatus] | None = Field(default=None, description="只看這些閱讀狀態，null 表示不篩選")
    categories: list[MangaCategory] | None = Field(default=None, description="只看這些分類，null 表示不篩選")
    min_rating: int | None = Field(default=None, ge=1, le=5, description="評分下限（含），沒評分的收藏會被排除")
    max_rating: int | None = Field(default=None, ge=1, le=5, description="評分上限（含），沒評分的收藏會被排除")


class SearchCollectionArgs(_CollectionFilterArgs):
    sort_by: Literal["rating", "last_read_at", "current_chapter", "created_at"] = "last_read_at"
    sort_order: Literal["asc", "desc"] = "desc"
    limit: int = Field(default=20, ge=1, le=50)


class CollectionStatsArgs(_CollectionFilterArgs):
    group_by: Literal["category", "status", "rating"] = Field(description="依哪個欄位分組計數")


class AssistantQueryRequest(CamelModel):
    question: str = Field(min_length=1, max_length=500)


class AssistantQueryResponse(CamelModel):
    answer: str
    items: list[CollectionItemResponse]
