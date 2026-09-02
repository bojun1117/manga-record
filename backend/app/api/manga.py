from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_admin, require_auth
from app.core.database import get_db
from app.schema.manga import MangaAdminResponse, MangaSearchResult, UpdateMangaRequest
from app.service import collection_service

router = APIRouter(prefix="/manga", tags=["manga"])


@router.get("/search", response_model=list[MangaSearchResult])
def search_manga(
    q: str = Query(min_length=1),
    _member_id: int = Depends(require_auth),
    db: Session = Depends(get_db),
) -> list[MangaSearchResult]:
    results = collection_service.search_manga(db, q)
    return [MangaSearchResult(id=m.id, title=m.title, category=m.category) for m in results]


@router.patch("/{manga_id}", response_model=MangaAdminResponse)
def update_manga(
    manga_id: int,
    payload: UpdateMangaRequest,
    _admin_id: int = Depends(require_admin),
    db: Session = Depends(get_db),
) -> MangaAdminResponse:
    manga = collection_service.update_manga(db, manga_id, payload.title, payload.category)
    return MangaAdminResponse(
        id=manga.id,
        title=manga.title,
        category=manga.category,
        created_at=manga.created_at,
        updated_at=manga.updated_at,
    )
