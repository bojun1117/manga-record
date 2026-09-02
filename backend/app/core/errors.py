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
    status_code = 409
    code = "ALREADY_IN_COLLECTION"


class DuplicateTitleError(AppError):
    status_code = 409
    code = "DUPLICATE_TITLE"
