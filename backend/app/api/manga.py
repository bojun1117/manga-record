from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_auth
from app.core.database import get_db
from app.schema.manga import MangaSearchResult
from app.service import collection_service

router = APIRouter(prefix="/manga", tags=["manga"])


@router.get("/search", response_model=list[MangaSearchResult])
def search_manga(
    q: str = Query(min_length=1),
    _member_id: int = Depends(require_auth),
    db: Session = Depends(get_db),
) -> list[MangaSearchResult]:
    """API.md §7。查無結果回空陣列，不是錯誤——前端用這個判斷「這是新漫畫」。"""
    results = collection_service.search_manga(db, q)
    return [MangaSearchResult(id=m.id, title=m.title, category=m.category) for m in results]
