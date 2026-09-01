from fastapi import Depends, FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.auth import router as auth_router
from app.api.collections import router as collections_router
from app.api.manga import router as manga_router
from app.core.database import get_db
from app.core.errors import AppError

app = FastAPI(title="Manga Record API")

# API.md §1.5：開發階段 `*`；EC2 有固定網址後收緊到正式 domain。
# allow_credentials 保持預設 False——auth 用 Authorization: Bearer header（見 AUTH.md），不靠 cookie。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(manga_router)
app.include_router(collections_router)


@app.exception_handler(AppError)
def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    """統一轉成 API.md §1.4 的錯誤格式。"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
    )


@app.exception_handler(RequestValidationError)
def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Pydantic 的 request body 驗證失敗，FastAPI 預設回 422，這裡改成 API.md 規定的 400 VALIDATION_ERROR。"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "request validation failed",
                "details": {"errors": jsonable_encoder(exc.errors())},
            }
        },
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/db")
def health_db(db: Session = Depends(get_db)) -> dict[str, str]:
    """驗收用：確認 FastAPI 真的能透過 SQLAlchemy 連上 RDS。"""
    db.execute(text("SELECT 1"))
    return {"status": "ok"}
