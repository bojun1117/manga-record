"""AI 助理的工具執行：資料範圍限定在自己的收藏、統計與 total/has_more 正確、參數錯誤回 is_error。"""

import json

from app.model import MangaCategory, ReadingStatus
from app.service import assistant_service
from tests.factories import make_entry, make_manga, make_member


def run_tools(monkeypatch, db, member_id: int, *calls: tuple[str, dict]):
    """用假的 run_assistant 依序執行工具，回傳 (每個工具的結果, answer_query 的回傳值)。"""
    outputs: list[tuple[str, bool]] = []

    def fake_run_assistant(question, execute_tool):
        for name, args in calls:
            outputs.append(execute_tool(name, args))
        return "answer"

    monkeypatch.setattr(assistant_service, "run_assistant", fake_run_assistant)
    result = assistant_service.answer_query(db, member_id, "question")
    return outputs, result


def test_stats_groups_only_my_collection(monkeypatch, db):
    me = make_member(db, "me")
    other = make_member(db, "other")
    for i in range(3):
        make_entry(db, me, make_manga(db, f"熱血{i}", MangaCategory.HOT_BLOODED), rating=4)
    make_entry(db, me, make_manga(db, "懸疑", MangaCategory.MYSTERY))
    for i in range(5):
        make_entry(db, other, make_manga(db, f"別人的愛情{i}", MangaCategory.ROMANCE))

    outputs, _ = run_tools(monkeypatch, db, me.id, ("collection_stats", {"group_by": "category"}))

    content, is_error = outputs[0]
    assert not is_error
    assert json.loads(content) == {
        "total": 4,
        "groups": [
            {"value": "hot_blooded", "count": 3, "avg_rating": 4.0},
            {"value": "mystery", "count": 1, "avg_rating": None},
        ],
    }


def test_search_reports_total_and_has_more(monkeypatch, db):
    me = make_member(db, "me")
    for i in range(5):
        make_entry(db, me, make_manga(db, f"追完{i}"), ReadingStatus.COMPLETED, rating=i + 1)
    make_entry(db, me, make_manga(db, "追讀中"))

    outputs, (answer, rows) = run_tools(
        monkeypatch,
        db,
        me.id,
        ("search_collection", {"statuses": ["completed"], "sort_by": "rating", "limit": 2}),
    )

    result = json.loads(outputs[0][0])
    assert (result["total"], result["returned"], result["has_more"]) == (5, 2, True)
    assert [item["rating"] for item in result["items"]] == [5, 4]
    assert answer == "answer"
    assert len(rows) == 2  # 最後一次搜尋的結果會顯示成卡片


def test_invalid_arguments_return_tool_error(monkeypatch, db):
    me = make_member(db, "me")

    outputs, _ = run_tools(
        monkeypatch,
        db,
        me.id,
        ("collection_stats", {"group_by": "bogus"}),
        ("unknown_tool", {}),
    )

    assert outputs[0][1] is True
    assert "Invalid arguments" in outputs[0][0]
    assert outputs[1] == ("Unknown tool: unknown_tool", True)
