from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_auth
from app.core.database import get_db
from app.schema.assistant import AssistantQueryRequest, AssistantQueryResponse
from app.schema.collection import build_collection_item_response
from app.service import assistant_service

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/query", response_model=AssistantQueryResponse)
def query_assistant(
    payload: AssistantQueryRequest,
    member_id: int = Depends(require_auth),
    db: Session = Depends(get_db),
) -> AssistantQueryResponse:
    answer, rows = assistant_service.answer_query(db, member_id, payload.question)
    return AssistantQueryResponse(
        answer=answer,
        items=[build_collection_item_response(entry, manga) for entry, manga in rows],
    )
