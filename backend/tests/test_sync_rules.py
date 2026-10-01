"""一鍵更新的純邏輯：解析過濾、只往前更新、比對。不需要資料庫。"""

import pytest

from app.core.chinese import normalize_chinese
from app.model import Manga, MemberManga, ReadingStatus
from app.schema.sync import ExtractedReadingRecord, ParsedReadingRecord
from app.service import sync_service


def record(
    title: str = "漫畫",
    chapter: float | None = None,
    volume: float | None = None,
    is_special: bool = False,
    source_text: str = "",
) -> ExtractedReadingRecord:
    return ExtractedReadingRecord(
        title=title, source_text=source_text, chapter=chapter, volume=volume, is_special=is_special
    )


def entry(
    entry_id: int = 1,
    status: ReadingStatus = ReadingStatus.READING,
    current_volume: int | None = None,
    current_chapter: int | None = None,
) -> MemberManga:
    return MemberManga(
        id=entry_id, status=status, current_volume=current_volume, current_chapter=current_chapter
    )


def parsed(normalized_title: str, chapter: int | None = None, volume: int | None = None) -> ParsedReadingRecord:
    return ParsedReadingRecord(
        source_title=normalized_title,
        source_text="",
        normalized_title=normalized_title,
        volume=volume,
        chapter=chapter,
    )


class TestUsableProgress:
    @pytest.mark.parametrize(
        ("rec", "expected"),
        [
            (record(chapter=107), (None, 107)),
            (record(volume=3), (3, None)),
            (record(volume=3, chapter=9), (3, 9)),
            (record(chapter=107.0), (None, 107)),
        ],
    )
    def test_keeps_whole_numbers(self, rec, expected):
        assert sync_service._usable_progress(rec) == expected

    @pytest.mark.parametrize(
        "rec",
        [
            record(chapter=50, is_special=True),  # 番外
            record(chapter=10.2),  # 非整數話數
            record(volume=2.5),  # 非整數卷數
            record(chapter=1),  # 第 1 話
            record(volume=1),  # 第 1 卷
            record(volume=1, chapter=5),  # 第 1 卷也略過
            record(),  # 沒有話數也沒有卷數
            record(chapter=-3),
            record(chapter=10000),
        ],
    )
    def test_drops_unusable_records(self, rec):
        assert sync_service._usable_progress(rec) is None


class TestForwardChanges:
    def test_chapter_moves_forward(self):
        assert sync_service._forward_changes(entry(current_chapter=100), None, 107) == (None, 107)

    def test_unrecorded_progress_counts_as_forward(self):
        assert sync_service._forward_changes(entry(), 2, 30) == (2, 30)

    def test_same_progress_is_not_a_change(self):
        assert sync_service._forward_changes(entry(current_chapter=100), None, 100) is None

    def test_behind_is_rejected(self):
        assert sync_service._forward_changes(entry(current_chapter=120), None, 114) is None

    def test_any_field_behind_rejects_the_whole_record(self):
        # 卷數前進但話數落後 → 不更新
        assert sync_service._forward_changes(entry(current_volume=2, current_chapter=10), 3, 9) is None

    def test_only_forward_fields_are_returned(self):
        assert sync_service._forward_changes(entry(current_volume=3, current_chapter=10), 3, 12) == (None, 12)


class TestParse:
    def test_filters_normalizes_and_keeps_latest_per_title(self, monkeypatch):
        monkeypatch.setattr(
            sync_service,
            "extract_reading_records",
            lambda raw: [
                record(" 恶女是提线木偶 ", chapter=14, source_text="第14话"),
                record("恶女是提线木偶", chapter=107, source_text="第107话"),
                record("BLUE LOCK", chapter=351, source_text="第351话试看"),
                record("越陷越深", chapter=10.2),
                record("番外漫画", volume=5, is_special=True),
            ],
        )

        result = sync_service.parse("raw")

        assert [(r.source_title, r.normalized_title, r.chapter, r.source_text) for r in result] == [
            ("恶女是提线木偶", "恶女是提线木偶", 107, "第107话"),
            ("BLUE LOCK", "blue lock", 351, "第351话试看"),
        ]

    def test_traditional_and_simplified_titles_share_a_key(self, monkeypatch):
        monkeypatch.setattr(
            sync_service,
            "extract_reading_records",
            lambda raw: [record("惡女是提線木偶", chapter=20), record("恶女是提线木偶", chapter=30)],
        )
        result = sync_service.parse("raw")
        assert len(result) == 1
        assert result[0].chapter == 30


class TestMatch:
    def rows(self, *items: tuple[MemberManga, str]) -> list[tuple[MemberManga, Manga]]:
        return [
            (e, Manga(id=e.id, title=title, normalized_title=normalize_chinese(title)))
            for e, title in items
        ]

    def test_lists_only_collected_manga_with_forward_progress(self):
        rows = self.rows(
            (entry(1, current_chapter=100), "惡女是提線木偶"),
            (entry(2, current_chapter=120), "作為敵國皇子的生存法則"),
            (entry(3, ReadingStatus.COMPLETED, current_chapter=10), "已追完的漫畫"),
            (entry(4, ReadingStatus.DROPPED, current_chapter=10), "棄坑的漫畫"),
            (entry(5, ReadingStatus.PLAN_TO_READ), "BLUE LOCK"),
        )
        records = [
            parsed("恶女是提线木偶", chapter=107),
            parsed("作为敌国皇子的生存法则", chapter=114),  # 落後
            parsed("已追完的漫画", chapter=50),
            parsed("弃坑的漫画", chapter=50),
            parsed("blue lock", chapter=351),
            parsed("不在收藏中", chapter=20),
        ]

        result = sync_service.match(records, rows)

        assert [(m.collection_id, m.current_chapter, m.new_chapter) for m in result.matched] == [
            (1, 100, 107),
            (5, None, 351),
        ]
        assert result.matched[0].title == "惡女是提線木偶"
        assert result.matched[1].status == ReadingStatus.PLAN_TO_READ

    def test_empty_when_nothing_matches(self):
        result = sync_service.match([parsed("不在收藏中", chapter=20)], self.rows((entry(1), "別的漫畫")))
        assert result.matched == []
