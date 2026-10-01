from pydantic import BaseModel, Field

from app.model import ReadingStatus
from app.schema.base import CamelModel

SYNC_RAW_MAX_LENGTH = 50_000


class ExtractedReadingRecord(BaseModel):
    title: str = Field(description="漫畫書名，照原文抄寫，不要翻譯或改寫")
    source_text: str = Field(description="這筆紀錄的章節原始文字，例如「第107话」「第12卷」「五卷番外」")
    chapter: float | None = Field(description="看到第幾話，照原文的數字（10.2 就填 10.2，中文數字轉阿拉伯數字），沒有話數填 null")
    volume: float | None = Field(description="看到第幾卷，照原文的數字，沒有卷數填 null")
    is_special: bool = Field(description="番外、特別篇、加筆、附錄、外傳、短篇、幕間這類非正篇章節填 true")


class ExtractedReadingRecords(BaseModel):
    records: list[ExtractedReadingRecord]


class ParsedReadingRecord(BaseModel):
    source_title: str
    source_text: str
    normalized_title: str
    volume: int | None
    chapter: int | None


class SyncPreviewRequest(CamelModel):
    raw: str = Field(min_length=1, max_length=SYNC_RAW_MAX_LENGTH)


class SyncMatchedItem(CamelModel):
    collection_id: int
    title: str
    status: ReadingStatus
    source_title: str
    source_text: str
    current_volume: int | None
    current_chapter: int | None
    new_volume: int | None
    new_chapter: int | None


class SyncPreviewResponse(CamelModel):
    matched: list[SyncMatchedItem]


class SyncUpdateItem(CamelModel):
    collection_id: int
    new_volume: int | None = Field(default=None, ge=0, le=9999)
    new_chapter: int | None = Field(default=None, ge=0, le=9999)


class SyncApplyRequest(CamelModel):
    updates: list[SyncUpdateItem] = Field(min_length=1, max_length=200)


class SyncApplyResponse(CamelModel):
    updated: int
