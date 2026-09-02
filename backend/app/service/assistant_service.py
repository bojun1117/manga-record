from sqlalchemy.orm import Session

from app.integration.llm.client import plan_query
from app.model import Manga, MemberManga
from app.repository import member_manga_repository


def answer_query(
    db: Session, member_id: int, question: str
) -> tuple[str, list[tuple[MemberManga, Manga]]]:
    plan = plan_query(question)
    if not plan.answerable:
        return plan.summary, []

    rows = member_manga_repository.list_for_assistant(
        db,
        member_id,
        plan.statuses,
        plan.categories,
        plan.min_rating,
        plan.max_rating,
        plan.sort_by,
        plan.sort_order,
        plan.limit,
    )
    return plan.summary, rows
