from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.chinese import normalize_chinese
from app.core.errors import NotFoundError
from app.integration.llm.client import extract_reading_records
from app.model import Manga, MemberManga, ReadingStatus
from app.repository import member_manga_repository
from app.schema.sync import (
    ExtractedReadingRecord,
    ParsedReadingRecord,
    SyncApplyRequest,
    SyncMatchedItem,
    SyncPreviewResponse,
)

MAX_PROGRESS = 9999
# 已追完、棄坑的收藏不列入同步清單
SKIPPED_STATUSES = (ReadingStatus.COMPLETED, ReadingStatus.DROPPED)


def _whole_number(value: float | None) -> int | None:
    if value is None:
        return None
    if value != int(value) or not 0 <= value <= MAX_PROGRESS:
        raise ValueError("not a whole number in range")
    return int(value)


def _usable_progress(record: ExtractedReadingRecord) -> tuple[int | None, int | None] | None:
    """回傳 (卷, 話)；番外、非整數、第 1 話或第 1 卷、沒有卷話數的紀錄回傳 None（直接丟掉）。"""
    if record.is_special:
        return None
    try:
        volume = _whole_number(record.volume)
        chapter = _whole_number(record.chapter)
    except ValueError:
        return None
    if volume is None and chapter is None:
        return None
    if chapter == 1 or volume == 1:
        return None
    return volume, chapter


def _forward_changes(
    entry: MemberManga, volume: int | None, chapter: int | None
) -> tuple[int | None, int | None] | None:
    """只往前更新：任何一項比收藏裡的進度落後，或完全沒有前進，就回傳 None。"""
    new_volume = new_chapter = None
    for new, current, field in ((volume, entry.current_volume, "volume"), (chapter, entry.current_chapter, "chapter")):
        if new is None:
            continue
        if current is not None and new < current:
            return None
        if current is None or new > current:
            if field == "volume":
                new_volume = new
            else:
                new_chapter = new
    if new_volume is None and new_chapter is None:
        return None
    return new_volume, new_chapter


# AI 解析：只把文字轉成結構化紀錄並過濾，不碰資料庫
def parse(raw: str) -> list[ParsedReadingRecord]:
    parsed: dict[str, ParsedReadingRecord] = {}
    for record in extract_reading_records(raw):
        progress = _usable_progress(record)
        if progress is None:
            continue
        volume, chapter = progress
        title = record.title.strip()
        normalized = normalize_chinese(title)

        existing = parsed.get(normalized)
        if existing is not None and (existing.chapter or 0, existing.volume or 0) >= (chapter or 0, volume or 0):
            continue
        parsed[normalized] = ParsedReadingRecord(
            source_title=title,
            source_text=record.source_text,
            normalized_title=normalized,
            volume=volume,
            chapter=chapter,
        )
    return list(parsed.values())


# 比對：純邏輯，不碰資料庫也不碰 AI
def match(records: list[ParsedReadingRecord], rows: list[tuple[MemberManga, Manga]]) -> SyncPreviewResponse:
    by_title = {manga.normalized_title: (entry, manga) for entry, manga in rows}
    matched: list[SyncMatchedItem] = []

    for record in records:
        # 只處理收藏裡比對得到的漫畫，比對不到的直接略過
        owned = by_title.get(record.normalized_title)
        if owned is None:
            continue

        entry, manga = owned
        if entry.status in SKIPPED_STATUSES:
            continue
        changes = _forward_changes(entry, record.volume, record.chapter)
        if changes is None:
            continue
        new_volume, new_chapter = changes
        matched.append(
            SyncMatchedItem(
                collection_id=entry.id,
                title=manga.title,
                status=entry.status,
                source_title=record.source_title,
                source_text=record.source_text,
                current_volume=entry.current_volume,
                current_chapter=entry.current_chapter,
                new_volume=new_volume,
                new_chapter=new_chapter,
            )
        )

    return SyncPreviewResponse(matched=matched)


def preview(db: Session, member_id: int, raw: str) -> SyncPreviewResponse:
    records = parse(raw)
    rows = member_manga_repository.list_all_with_manga(db, member_id)
    return match(records, rows)


def _apply_progress(entry: MemberManga, volume: int | None, chapter: int | None, now: datetime) -> bool:
    changes = _forward_changes(entry, volume, chapter)
    if changes is None:
        return False
    new_volume, new_chapter = changes
    if new_volume is not None:
        entry.current_volume = new_volume
    if new_chapter is not None:
        entry.current_chapter = new_chapter
    if entry.status == ReadingStatus.PLAN_TO_READ:
        entry.status = ReadingStatus.READING
    entry.last_read_at = now
    return True


def apply(db: Session, member_id: int, payload: SyncApplyRequest) -> dict[str, int]:
    rows = member_manga_repository.list_all_with_manga(db, member_id)
    by_id = {entry.id: entry for entry, _ in rows}
    now = datetime.now(timezone.utc)

    updated = 0
    for item in payload.updates:
        entry = by_id.get(item.collection_id)
        if entry is None:
            raise NotFoundError("collection entry not found")
        if _apply_progress(entry, item.new_volume, item.new_chapter, now):
            updated += 1

    db.commit()
    return {"updated": updated}
