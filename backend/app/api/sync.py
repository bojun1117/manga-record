from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_auth
from app.core.database import get_db
from app.schema.sync import SyncApplyRequest, SyncApplyResponse, SyncPreviewRequest, SyncPreviewResponse
from app.service import sync_service

router = APIRouter(prefix="/collections/sync", tags=["sync"])


@router.post("/preview", response_model=SyncPreviewResponse)
def preview_sync(
    payload: SyncPreviewRequest,
    member_id: int = Depends(require_auth),
    db: Session = Depends(get_db),
) -> SyncPreviewResponse:
    return sync_service.preview(db, member_id, payload.raw)


@router.post("/apply", response_model=SyncApplyResponse)
def apply_sync(
    payload: SyncApplyRequest,
    member_id: int = Depends(require_auth),
    db: Session = Depends(get_db),
) -> SyncApplyResponse:
    return SyncApplyResponse(**sync_service.apply(db, member_id, payload))
