from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import require_auth
from app.core.database import get_db
from app.core.errors import NotFoundError
from app.repository import member_repository
from app.schema.auth import (
    LoginRequest,
    MemberResponse,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from app.service import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> RegisterResponse:
    member = auth_service.register(db, payload.username, payload.password)
    return RegisterResponse(id=member.id, username=member.username)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    token = auth_service.login(db, payload.username, payload.password)
    return TokenResponse(token=token)


@router.get("/me", response_model=MemberResponse)
def me(
    member_id: int = Depends(require_auth),
    db: Session = Depends(get_db),
) -> MemberResponse:
    member = member_repository.get_by_id(db, member_id)
    if member is None:
        raise NotFoundError("member not found")
    return MemberResponse(id=member.id, username=member.username, is_admin=member.is_admin)
