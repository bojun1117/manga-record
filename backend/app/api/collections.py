from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import require_auth
from app.core.database import get_db
from app.model import Manga, MemberManga
from app.schema.collection import (
    CollectionItemResponse,
    CreateCollectionRequest,
    UpdateCollectionRequest,
)
from app.service import collection_service

router = APIRouter(prefix="/collections", tags=["collections"])


def _to_response(entry: MemberManga, manga: Manga) -> CollectionItemResponse:
    return CollectionItemResponse(
        id=entry.id,
        manga_id=manga.id,
        title=manga.title,
        category=manga.category,
        status=entry.status,
        current_volume=entry.current_volume,
        current_chapter=entry.current_chapter,
        rating=entry.rating,
        last_read_at=entry.last_read_at,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


@router.get("", response_model=list[CollectionItemResponse])
def list_collections(
    member_id: int = Depends(require_auth),
    db: Session = Depends(get_db),
) -> list[CollectionItemResponse]:
    rows = collection_service.list_collections(db, member_id)
    return [_to_response(entry, manga) for entry, manga in rows]


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
    return _to_response(entry, manga)


@router.patch("/{collection_id}", response_model=CollectionItemResponse)
def update_collection(
    collection_id: int,
    payload: UpdateCollectionRequest,
    member_id: int = Depends(require_auth),
    db: Session = Depends(get_db),
) -> CollectionItemResponse:
    # exclude_unset=True 是 partial update 的關鍵：只有 request body 裡真的出現的欄位才會進這個 dict
    # （API.md §1.3：null 代表明確清空、key 不存在代表不要動）
    fields = payload.model_dump(exclude_unset=True)
    entry, manga = collection_service.update_collection(db, member_id, collection_id, fields)
    return _to_response(entry, manga)


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_collection(
    collection_id: int,
    member_id: int = Depends(require_auth),
    db: Session = Depends(get_db),
) -> None:
    collection_service.delete_collection(db, member_id, collection_id)
