from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_admin, require_auth
from app.core.database import get_db
from app.schema.manga import (
    MangaAdminResponse,
    MangaListResponse,
    MangaSearchResult,
    UpdateMangaRequest,
)
from app.service import collection_service

router = APIRouter(prefix="/manga", tags=["manga"])

PAGE_SIZE = 20


@router.get("", response_model=MangaListResponse)
def list_manga(
    page: int = Query(default=1, ge=1),
    _admin_id: int = Depends(require_admin),
    db: Session = Depends(get_db),
) -> MangaListResponse:
    items, total = collection_service.list_manga(db, page, PAGE_SIZE)
    return MangaListResponse(
        items=[MangaSearchResult(id=m.id, title=m.title, category=m.category) for m in items],
        page=page,
        page_size=PAGE_SIZE,
        total=total,
    )


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
