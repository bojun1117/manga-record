from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_auth
from app.core.database import get_db
from app.model import MangaCategory, ReadingStatus
from app.schema.collection import (
    CollectionItemResponse,
    CollectionListResponse,
    CollectionStatsResponse,
    CreateCollectionRequest,
    UpdateCollectionRequest,
    build_collection_item_response,
)
from app.service import collection_service

router = APIRouter(prefix="/collections", tags=["collections"])

PAGE_SIZE = 30


@router.get("", response_model=CollectionListResponse)
def list_collections(
    status: list[ReadingStatus] | None = Query(default=None),
    category: MangaCategory | None = Query(default=None),
    q: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    member_id: int = Depends(require_auth),
    db: Session = Depends(get_db),
) -> CollectionListResponse:
    rows, total = collection_service.list_collections_page(
        db, member_id, status, category, q, page, PAGE_SIZE
    )
    return CollectionListResponse(
        items=[build_collection_item_response(entry, manga) for entry, manga in rows],
        page=page,
        page_size=PAGE_SIZE,
        total=total,
    )


@router.get("/stats", response_model=CollectionStatsResponse)
def collections_stats(
    member_id: int = Depends(require_auth),
    db: Session = Depends(get_db),
) -> CollectionStatsResponse:
    return CollectionStatsResponse(**collection_service.get_collection_stats(db, member_id))


@router.post("", response_model=CollectionItemResponse, status_code=status.HTTP_201_CREATED)
def create_collection(
    payload: CreateCollectionRequest,
    member_id: int = Depends(require_auth),
    db: Session = Depends(get_db),
) -> CollectionItemResponse:
    entry, manga = collection_service.create_collection(
        db,
        member_id,
        payload.manga_name,
        payload.category,
        payload.status,
        payload.current_volume,
        payload.current_chapter,
        payload.rating,
    )
    return build_collection_item_response(entry, manga)


@router.patch("/{collection_id}", response_model=CollectionItemResponse)
def update_collection(
    collection_id: int,
    payload: UpdateCollectionRequest,
    member_id: int = Depends(require_auth),
    db: Session = Depends(get_db),
) -> CollectionItemResponse:
    fields = payload.model_dump(exclude_unset=True)
    entry, manga = collection_service.update_collection(db, member_id, collection_id, fields)
    return build_collection_item_response(entry, manga)


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_collection(
    collection_id: int,
    member_id: int = Depends(require_auth),
    db: Session = Depends(get_db),
) -> None:
    collection_service.delete_collection(db, member_id, collection_id)
