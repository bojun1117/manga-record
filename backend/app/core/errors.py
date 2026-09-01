# 統一的應用層錯誤型別，對應 API.md §1.4 / §12 的錯誤格式。
# service 層丟這些例外，main.py 的 exception handler 統一轉成
# {"error": {"code", "message", "details"}} 格式，狀態碼由 status_code 決定。

from typing import Any


class AppError(Exception):
    status_code: int = 500
    code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class ValidationAppError(AppError):
    status_code = 400
    code = "VALIDATION_ERROR"


class UnauthorizedError(AppError):
    status_code = 401
    code = "UNAUTHORIZED"


class ForbiddenError(AppError):
    status_code = 403
    code = "FORBIDDEN"


class NotFoundError(AppError):
    status_code = 404
    code = "NOT_FOUND"


class UsernameTakenError(AppError):
    status_code = 409
    code = "USERNAME_TAKEN"


class AlreadyInCollectionError(AppError):
    """Phase 4 會用到（POST /collections 撞 UNIQUE(member_id, manga_id)），先定義在這裡。"""

    status_code = 409
    code = "ALREADY_IN_COLLECTION"
