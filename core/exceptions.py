"""
core/exceptions.py
==================
Custom exception hierarchy for the TAMS application.

Using a typed exception tree makes error handling precise across
services, repositories, and the UI layer.
"""


class TAMSError(Exception):
    """Base exception for all TAMS application errors."""

    def __init__(self, message: str = "An unexpected error occurred.") -> None:
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:
        return self.message


# ---------------------------------------------------------------------------
# Authentication & Authorization
# ---------------------------------------------------------------------------

class AuthenticationError(TAMSError):
    """Raised when login credentials are invalid."""

    def __init__(self, message: str = "Invalid username or password.") -> None:
        super().__init__(message)


class AccountLockedError(AuthenticationError):
    """Raised when a user account is locked due to too many failed attempts."""

    def __init__(self, minutes_remaining: int = 0) -> None:
        msg = (
            f"Account is locked. Please try again in {minutes_remaining} minute(s)."
            if minutes_remaining > 0
            else "Account is locked. Please contact an administrator."
        )
        super().__init__(msg)
        self.minutes_remaining = minutes_remaining


class PermissionDeniedError(TAMSError):
    """Raised when a user tries to perform an action they are not allowed to."""

    def __init__(self, action: str = "", module: str = "") -> None:
        if action and module:
            msg = f"You do not have permission to '{action}' in the '{module}' module."
        elif module:
            msg = f"You do not have access to the '{module}' module."
        else:
            msg = "Permission denied."
        super().__init__(msg)
        self.action = action
        self.module = module


class SessionExpiredError(TAMSError):
    """Raised when the user's session has timed out."""

    def __init__(self) -> None:
        super().__init__(
            "Your session has expired due to inactivity. Please log in again."
        )


# ---------------------------------------------------------------------------
# Database & Repository
# ---------------------------------------------------------------------------

class DatabaseError(TAMSError):
    """Raised when a database operation fails unexpectedly."""

    def __init__(self, message: str = "A database error occurred.") -> None:
        super().__init__(message)


class RecordNotFoundError(TAMSError):
    """Raised when a requested record does not exist."""

    def __init__(self, model: str = "Record", record_id: str = "") -> None:
        if record_id:
            msg = f"{model} with ID '{record_id}' was not found."
        else:
            msg = f"{model} was not found."
        super().__init__(msg)
        self.model = model
        self.record_id = record_id


class DuplicateRecordError(TAMSError):
    """Raised when a unique constraint would be violated."""

    def __init__(self, field: str = "", value: str = "") -> None:
        if field and value:
            msg = f"A record with {field} = '{value}' already exists."
        else:
            msg = "A duplicate record already exists."
        super().__init__(msg)
        self.field = field
        self.value = value


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class ValidationError(TAMSError):
    """Raised when input data fails validation."""

    def __init__(
        self,
        message: str = "Validation failed.",
        field: str = "",
        errors: dict | None = None,
    ) -> None:
        if field:
            message = f"{field}: {message}"
        super().__init__(message)
        self.field = field
        self.errors: dict = errors or {}


class RequiredFieldError(ValidationError):
    """Raised when a required field is missing or empty."""

    def __init__(self, field: str) -> None:
        super().__init__(f"'{field}' is required.", field=field)


class InvalidFormatError(ValidationError):
    """Raised when a field value has an invalid format."""

    def __init__(self, field: str, expected_format: str = "") -> None:
        msg = f"'{field}' has an invalid format."
        if expected_format:
            msg += f" Expected: {expected_format}"
        super().__init__(msg, field=field)


# ---------------------------------------------------------------------------
# Business Logic
# ---------------------------------------------------------------------------

class BusinessRuleError(TAMSError):
    """Raised when a business rule is violated."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class InsufficientFundsError(BusinessRuleError):
    """Raised when a payment cannot be processed due to insufficient balance."""

    def __init__(self, required: float = 0, available: float = 0) -> None:
        super().__init__(
            f"Insufficient funds. Required: {required:.2f}, Available: {available:.2f}"
        )
        self.required = required
        self.available = available


class BookingConflictError(BusinessRuleError):
    """Raised when a booking conflicts with an existing reservation."""

    def __init__(self, message: str = "Booking conflict detected.") -> None:
        super().__init__(message)


# ---------------------------------------------------------------------------
# File / Document
# ---------------------------------------------------------------------------

class FileError(TAMSError):
    """Raised when a file operation fails."""

    def __init__(self, message: str = "File operation failed.") -> None:
        super().__init__(message)


class FileSizeTooLargeError(FileError):
    """Raised when an uploaded file exceeds the allowed size."""

    def __init__(self, max_mb: float = 5.0) -> None:
        super().__init__(f"File size exceeds the maximum allowed size of {max_mb} MB.")
        self.max_mb = max_mb


class UnsupportedFileTypeError(FileError):
    """Raised when an uploaded file has an unsupported type."""

    def __init__(self, file_type: str = "", allowed: list | None = None) -> None:
        allowed_str = ", ".join(allowed) if allowed else "known types"
        super().__init__(
            f"File type '{file_type}' is not supported. Allowed: {allowed_str}."
        )


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

class ReportError(TAMSError):
    """Raised when report generation fails."""

    def __init__(self, message: str = "Report generation failed.") -> None:
        super().__init__(message)


# ---------------------------------------------------------------------------
# Backup
# ---------------------------------------------------------------------------

class BackupError(TAMSError):
    """Raised when a backup or restore operation fails."""

    def __init__(self, message: str = "Backup operation failed.") -> None:
        super().__init__(message)
