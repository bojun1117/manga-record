import json

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.integration.llm.client import run_assistant
from app.model import Manga, MemberManga
from app.repository import member_manga_repository
from app.schema.assistant import CollectionStatsArgs, SearchCollectionArgs


def answer_query(
    db: Session, member_id: int, question: str
) -> tuple[str, list[tuple[MemberManga, Manga]]]:
    # 最後一次 search_collection 的結果會以卡片顯示在回答下方
    shown_rows: list[tuple[MemberManga, Manga]] = []

    def search_collection(args: SearchCollectionArgs) -> dict:
        total = member_manga_repository.count_for_assistant(
            db, member_id, args.statuses, args.categories, args.min_rating, args.max_rating
        )
        rows = member_manga_repository.list_for_assistant(
            db,
            member_id,
            args.statuses,
            args.categories,
            args.min_rating,
            args.max_rating,
            args.sort_by,
            args.sort_order,
            args.limit,
        )
        shown_rows[:] = rows
        return {
            "total": total,
            "returned": len(rows),
            "has_more": total > len(rows),
            "items": [
                {
                    "title": manga.title,
                    "category": manga.category.value,
                    "status": entry.status.value,
                    "current_volume": entry.current_volume,
                    "current_chapter": entry.current_chapter,
                    "rating": entry.rating,
                    "last_read_at": entry.last_read_at.isoformat(),
                }
                for entry, manga in rows
            ],
        }

    def collection_stats(args: CollectionStatsArgs) -> dict:
        groups = member_manga_repository.stats_for_assistant(
            db,
            member_id,
            args.group_by,
            args.statuses,
            args.categories,
            args.min_rating,
            args.max_rating,
        )
        return {
            "total": sum(count for _, count, _ in groups),
            "groups": [
                {
                    "value": getattr(value, "value", value) if value is not None else "unrated",
                    "count": count,
                    "avg_rating": round(avg, 2) if avg is not None else None,
                }
                for value, count, avg in groups
            ],
        }

    def execute_tool(name: str, raw_args: dict) -> tuple[str, bool]:
        try:
            if name == "search_collection":
                result = search_collection(SearchCollectionArgs.model_validate(raw_args))
            elif name == "collection_stats":
                result = collection_stats(CollectionStatsArgs.model_validate(raw_args))
            else:
                return f"Unknown tool: {name}", True
        except ValidationError as exc:
            return f"Invalid arguments: {exc}", True
        return json.dumps(result, ensure_ascii=False), False

    answer = run_assistant(question, execute_tool)
    return answer, shown_rows
