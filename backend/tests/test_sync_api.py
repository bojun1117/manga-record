"""一鍵更新的兩支 API：preview（不寫入）、apply（同一交易、只往前更新、只能改自己的收藏）。"""

from datetime import datetime, timedelta, timezone

from app.model import MemberManga, ReadingStatus
from app.schema.sync import ExtractedReadingRecord
from app.service import sync_service
from tests.factories import auth_header, make_entry, make_manga, make_member


def fake_extract(monkeypatch, *records: tuple[str, float | None, float | None]) -> None:
    monkeypatch.setattr(
        sync_service,
        "extract_reading_records",
        lambda raw: [
            ExtractedReadingRecord(title=t, source_text=f"第{c}话", chapter=c, volume=v, is_special=False)
            for t, c, v in records
        ],
    )


class TestPreview:
    def test_returns_matched_items_without_writing(self, client, db, monkeypatch):
        me = make_member(db, "me")
        other = make_member(db, "other")
        akujo = make_entry(db, me, make_manga(db, "惡女是提線木偶"), current_chapter=100)
        make_entry(db, me, make_manga(db, "已追完"), ReadingStatus.COMPLETED, current_chapter=10)
        make_entry(db, other, make_manga(db, "別人的漫畫"), current_chapter=1)
        fake_extract(monkeypatch, ("恶女是提线木偶", 107, None), ("已追完", 50, None), ("别人的漫画", 50, None))

        res = client.post("/collections/sync/preview", json={"raw": "..."}, headers=auth_header(me))

        assert res.status_code == 200
        assert res.json() == {
            "matched": [
                {
                    "collectionId": akujo.id,
                    "title": "惡女是提線木偶",
                    "status": "reading",
                    "sourceTitle": "恶女是提线木偶",
                    "sourceText": "第107话",
                    "currentVolume": None,
                    "currentChapter": 100,
                    "newVolume": None,
                    "newChapter": 107,
                }
            ]
        }
        db.refresh(akujo)
        assert akujo.current_chapter == 100

    def test_requires_login(self, client):
        assert client.post("/collections/sync/preview", json={"raw": "..."}).status_code == 401

    def test_rejects_too_long_input(self, client, db):
        me = make_member(db, "me")
        res = client.post("/collections/sync/preview", json={"raw": "x" * 50_001}, headers=auth_header(me))
        assert res.status_code == 400
        assert res.json()["error"]["code"] == "VALIDATION_ERROR"


class TestApply:
    def test_updates_progress_status_and_last_read_at(self, client, db):
        me = make_member(db, "me")
        planned = make_entry(db, me, make_manga(db, "BLUE LOCK"), ReadingStatus.PLAN_TO_READ)
        reading = make_entry(db, me, make_manga(db, "刺客信條"), current_volume=2, current_chapter=10)
        before = datetime.now(timezone.utc) - timedelta(seconds=1)

        res = client.post(
            "/collections/sync/apply",
            json={
                "updates": [
                    {"collectionId": planned.id, "newVolume": None, "newChapter": 351},
                    {"collectionId": reading.id, "newVolume": 3, "newChapter": None},
                ]
            },
            headers=auth_header(me),
        )

        assert res.status_code == 200
        assert res.json() == {"updated": 2}
        db.refresh(planned)
        db.refresh(reading)
        assert (planned.status, planned.current_chapter) == (ReadingStatus.READING, 351)
        assert planned.last_read_at > before
        assert (reading.current_volume, reading.current_chapter) == (3, 10)

    def test_never_moves_progress_backwards(self, client, db):
        me = make_member(db, "me")
        entry = make_entry(db, me, make_manga(db, "海賊王"), current_chapter=1100)

        res = client.post(
            "/collections/sync/apply",
            json={"updates": [{"collectionId": entry.id, "newChapter": 900}]},
            headers=auth_header(me),
        )

        assert res.json() == {"updated": 0}
        db.refresh(entry)
        assert entry.current_chapter == 1100

    def test_other_members_entry_fails_the_whole_batch(self, client, db):
        me = make_member(db, "me")
        other = make_member(db, "other")
        mine = make_entry(db, me, make_manga(db, "我的漫畫"), current_chapter=10)
        theirs = make_entry(db, other, make_manga(db, "別人的漫畫"), current_chapter=10)
        db.commit()  # 先提交測試資料，之後的 rollback 只會撤銷 API 做的變更

        res = client.post(
            "/collections/sync/apply",
            json={
                "updates": [
                    {"collectionId": mine.id, "newChapter": 20},
                    {"collectionId": theirs.id, "newChapter": 20},
                ]
            },
            headers=auth_header(me),
        )

        assert res.status_code == 404
        db.rollback()  # 等同請求結束時 get_db 關閉 session
        assert db.get(MemberManga, mine.id).current_chapter == 10
        assert db.get(MemberManga, theirs.id).current_chapter == 10

    def test_rejects_empty_updates(self, client, db):
        me = make_member(db, "me")
        res = client.post("/collections/sync/apply", json={"updates": []}, headers=auth_header(me))
        assert res.status_code == 400
