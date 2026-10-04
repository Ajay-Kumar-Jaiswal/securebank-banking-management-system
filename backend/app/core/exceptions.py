from datetime import datetime, timezone
from typing import Optional, List
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


class BankingException(Exception):
    """Base exception for banking business logic errors."""
    def __init__(self, message: str, status_code: int = 400, error_code: str = "BAD_REQUEST", details: Optional[List[str]] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or []


class UserNotFoundException(BankingException):
    def __init__(self, message: str = "User not found."):
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND, error_code="USER_NOT_FOUND")


class AccountNotFoundException(BankingException):
    def __init__(self, message: str = "Account not found."):
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND, error_code="ACCOUNT_NOT_FOUND")


class BeneficiaryNotFoundException(BankingException):
    def __init__(self, message: str = "Beneficiary not found or does not belong to you."):
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND, error_code="BENEFICIARY_NOT_FOUND")


class InsufficientBalanceException(BankingException):
    def __init__(self, message: str = "Insufficient balance for this operation."):
        super().__init__(message, status_code=status.HTTP_400_BAD_REQUEST, error_code="INSUFFICIENT_BALANCE")


class InvalidAccountStatusException(BankingException):
    def __init__(self, message: str = "Account status does not allow this operation."):
        super().__init__(message, status_code=status.HTTP_400_BAD_REQUEST, error_code="INVALID_ACCOUNT_STATUS")


class DuplicateEmailException(BankingException):
    def __init__(self, message: str = "An account with this email already exists."):
        super().__init__(message, status_code=status.HTTP_409_CONFLICT, error_code="DUPLICATE_EMAIL")


class DuplicateAccountException(BankingException):
    def __init__(self, message: str = "Could not generate a unique account number, please retry."):
        super().__init__(message, status_code=status.HTTP_409_CONFLICT, error_code="DUPLICATE_ACCOUNT")


class InvalidCredentialsException(BankingException):
    def __init__(self, message: str = "Invalid email or password."):
        super().__init__(message, status_code=status.HTTP_401_UNAUTHORIZED, error_code="INVALID_CREDENTIALS")


class UnauthorizedAccountAccessException(BankingException):
    def __init__(self, message: str = "You do not have permission to access this account."):
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN, error_code="FORBIDDEN")


class PermissionDeniedException(BankingException):
    def __init__(self, message: str = "Access denied. Insufficient permissions."):
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN, error_code="FORBIDDEN")


class InvalidTransactionException(BankingException):
    def __init__(self, message: str = "Invalid transaction parameters."):
        super().__init__(message, status_code=status.HTTP_400_BAD_REQUEST, error_code="INVALID_TRANSACTION")


class ClosureRequestException(BankingException):
    def __init__(self, message: str = "Account closure request cannot be processed."):
        super().__init__(message, status_code=status.HTTP_400_BAD_REQUEST, error_code="CLOSURE_REQUEST_ERROR")


def build_error_response(status_code: int, error_code: str, message: str, details: Optional[List[str]] = None) -> JSONResponse:
    content = {
        "status": status_code,
        "error": error_code,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if details:
        content["details"] = details
    return JSONResponse(status_code=status_code, content=content)


async def banking_exception_handler(request: Request, exc: BankingException) -> JSONResponse:
    return build_error_response(
        status_code=exc.status_code,
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = []
    for err in exc.errors():
        loc = " -> ".join(str(item) for item in err.get("loc", []))
        msg = err.get("msg", "")
        details.append(f"{loc}: {msg}")
    return build_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code="VALIDATION_ERROR",
        message="Request validation failed.",
        details=details,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return build_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code="INTERNAL_SERVER_ERROR",
        message=f"An unexpected error occurred: {str(exc)}",
    )
