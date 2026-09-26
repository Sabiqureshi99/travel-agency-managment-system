"""
services/auth_service.py
=========================
Authentication and session management service.

Handles:
- User login with brute-force lockout
- Session management (in-memory, per-process)
- Password hashing/verification via bcrypt
- Activity logging on every auth event
- Admins can reset passwords and unlock accounts
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select

from config.database import get_session
from core.exceptions import (
    AuthenticationError,
    AccountLockedError,
    ValidationError,
    RecordNotFoundError,
)
from models.user import User, ActivityLog
from utils.encryption import hash_password, verify_password, generate_session_id

logger = logging.getLogger(__name__)


class Session:
    """Represents an authenticated user session."""

    def __init__(self, user: User) -> None:
        self.session_id: str = generate_session_id()
        self.user: User = user
        self.created_at: datetime = datetime.now(timezone.utc)
        self.last_activity: datetime = datetime.now(timezone.utc)

    def touch(self) -> None:
        """Update the last activity timestamp."""
        self.last_activity = datetime.now(timezone.utc)

    def is_expired(self, timeout_minutes: int) -> bool:
        """Check whether the session has been idle for too long."""
        from config.settings import settings
        idle_seconds = (
            datetime.now(timezone.utc) - self.last_activity
        ).total_seconds()
        return idle_seconds > (timeout_minutes * 60)


class AuthService:
    """
    Singleton authentication service.

    Maintains the currently active session in memory (single-process desktop
    app). On a multi-workstation setup this can be extended to use Redis or a
    shared sessions table.
    """

    _instance: Optional["AuthService"] = None
    _current_session: Optional[Session] = None

    def __new__(cls) -> "AuthService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ------------------------------------------------------------------
    # Login / Logout
    # ------------------------------------------------------------------

    def login(self, username: str, password: str) -> User:
        """
        Authenticate a user with username and password.

        Args:
            username: The username to authenticate.
            password: The plain-text password.

        Returns:
            The authenticated User model instance.

        Raises:
            ValidationError: If username or password is empty.
            AccountLockedError: If the account is temporarily locked.
            AuthenticationError: If credentials are invalid.
        """
        if not username or not username.strip():
            raise ValidationError("Username is required.", field="username")
        if not password:
            raise ValidationError("Password is required.", field="password")

        username = username.strip().lower()

        with get_session() as session:
            stmt = select(User).where(
                User.username == username,
                User.is_deleted.is_(False),
            )
            user: Optional[User] = session.execute(stmt).scalar_one_or_none()

            if user is None:
                logger.warning("Login failed — unknown user: %s", username)
                self._log_activity(
                    session,
                    user_id=None,
                    action="LOGIN_FAILED",
                    module="auth",
                    description=f"Login attempt for unknown user '{username}'.",
                )
                raise AuthenticationError()

            # Check account status
            if user.status == "Inactive":
                raise AuthenticationError(
                    "Your account has been deactivated. "
                    "Please contact your administrator."
                )

            # Check if locked
            if user.locked_until:
                now = datetime.now(timezone.utc)
                locked_until = (
                    user.locked_until.replace(tzinfo=timezone.utc)
                    if user.locked_until.tzinfo is None
                    else user.locked_until
                )
                if now < locked_until:
                    remaining = int((locked_until - now).total_seconds() / 60) + 1
                    raise AccountLockedError(remaining)
                else:
                    # Lock expired — clear it
                    user.locked_until = None
                    user.failed_login_attempts = 0

            # Verify password
            if not verify_password(password, user.password_hash):
                user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
                logger.warning(
                    "Login failed — wrong password for user '%s' (attempt %d).",
                    username,
                    user.failed_login_attempts,
                )

                from config.settings import settings
                max_attempts = settings.security.max_login_attempts
                lockout_minutes = settings.security.lockout_duration_minutes

                if user.failed_login_attempts >= max_attempts:
                    from datetime import timedelta
                    user.locked_until = datetime.now(timezone.utc) + timedelta(
                        minutes=lockout_minutes
                    )
                    user.status = "Locked"
                    self._log_activity(
                        session,
                        user_id=user.id,
                        action="ACCOUNT_LOCKED",
                        module="auth",
                        description=(
                            f"Account locked after {max_attempts} failed login attempts."
                        ),
                    )
                    session.flush()
                    raise AccountLockedError(lockout_minutes)

                session.flush()
                raise AuthenticationError()

            # Success — reset counters, update last login
            user.failed_login_attempts = 0
            user.locked_until = None
            user.status = "Active"
            user.last_login = datetime.now(timezone.utc)

            self._log_activity(
                session,
                user_id=user.id,
                action="LOGIN",
                module="auth",
                description=f"User '{username}' logged in successfully.",
            )
            session.flush()

            # Keep the user detached from the session so it can be used freely
            session.expunge(user)

        # Create in-memory session
        self._current_session = Session(user)
        logger.info("User '%s' authenticated. Session ID: %s", username, self._current_session.session_id)
        return user

    def logout(self) -> None:
        """Clear the current session."""
        if self._current_session:
            user = self._current_session.user
            with get_session() as session:
                self._log_activity(
                    session,
                    user_id=user.id,
                    action="LOGOUT",
                    module="auth",
                    description=f"User '{user.username}' logged out.",
                )
            logger.info("User '%s' logged out.", user.username)
            self._current_session = None

    # ------------------------------------------------------------------
    # Session Access
    # ------------------------------------------------------------------

    @property
    def current_user(self) -> Optional[User]:
        """Return the currently logged-in User or None."""
        if self._current_session:
            self._current_session.touch()
            return self._current_session.user
        return None

    @property
    def current_session(self) -> Optional[Session]:
        """Return the active Session object or None."""
        return self._current_session

    def is_authenticated(self) -> bool:
        """True if a user is currently logged in."""
        return self._current_session is not None

    def check_session_timeout(self) -> bool:
        """
        Check if the current session has timed out.

        Returns:
            True if timed out (and session has been cleared), False if still valid.
        """
        if self._current_session is None:
            return True
        from config.settings import settings
        if self._current_session.is_expired(settings.security.session_timeout_minutes):
            logger.info("Session timed out for user '%s'.", self._current_session.user.username)
            self._current_session = None
            return True
        return False

    def touch_session(self) -> None:
        """Reset the session idle timer (call on every user action)."""
        if self._current_session:
            self._current_session.touch()

    # ------------------------------------------------------------------
    # Password Management
    # ------------------------------------------------------------------

    def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str,
    ) -> None:
        """
        Change a user's own password (requires current password verification).

        Args:
            user_id: The user's UUID.
            current_password: Current plain-text password.
            new_password: New plain-text password.

        Raises:
            ValidationError: If new password is too short.
            AuthenticationError: If current password is wrong.
            RecordNotFoundError: If user not found.
        """
        from config.settings import settings

        if len(new_password) < settings.security.password_min_length:
            raise ValidationError(
                f"Password must be at least {settings.security.password_min_length} characters.",
                field="new_password",
            )

        with get_session() as session:
            user = session.get(User, user_id)
            if not user:
                raise RecordNotFoundError("User", user_id)

            if not verify_password(current_password, user.password_hash):
                raise AuthenticationError("Current password is incorrect.")

            user.password_hash = hash_password(new_password)
            self._log_activity(
                session,
                user_id=user_id,
                action="PASSWORD_CHANGED",
                module="auth",
                description="User changed their password.",
            )

    def admin_reset_password(
        self, admin_user: User, target_user_id: str, new_password: str
    ) -> None:
        """
        Admin resets a user's password without needing the old one.

        Args:
            admin_user: The admin performing the action.
            target_user_id: UUID of the user whose password is being reset.
            new_password: The new plain-text password.
        """
        from core.permissions import has_permission, Modules, Actions
        from config.settings import settings

        if not has_permission(admin_user, Modules.EMPLOYEES, Actions.EDIT):
            from core.exceptions import PermissionDeniedError
            raise PermissionDeniedError(Actions.EDIT, Modules.EMPLOYEES)

        if len(new_password) < settings.security.password_min_length:
            raise ValidationError(
                f"Password must be at least {settings.security.password_min_length} characters.",
                field="new_password",
            )

        with get_session() as session:
            user = session.get(User, target_user_id)
            if not user:
                raise RecordNotFoundError("User", target_user_id)
            user.password_hash = hash_password(new_password)
            user.failed_login_attempts = 0
            user.locked_until = None
            if user.status == "Locked":
                user.status = "Active"

            self._log_activity(
                session,
                user_id=admin_user.id,
                action="PASSWORD_RESET",
                module="auth",
                description=f"Admin '{admin_user.username}' reset password for user '{user.username}'.",
                record_id=target_user_id,
            )

    def unlock_account(self, admin_user: User, target_user_id: str) -> None:
        """Admin unlocks a locked account."""
        with get_session() as session:
            user = session.get(User, target_user_id)
            if not user:
                raise RecordNotFoundError("User", target_user_id)
            user.locked_until = None
            user.failed_login_attempts = 0
            user.status = "Active"
            self._log_activity(
                session,
                user_id=admin_user.id,
                action="ACCOUNT_UNLOCKED",
                module="auth",
                description=f"Admin unlocked account for user '{user.username}'.",
                record_id=target_user_id,
            )

    # ------------------------------------------------------------------
    # User Management
    # ------------------------------------------------------------------

    def get_all_users(self) -> list[User]:
        with get_session() as session:
            stmt = select(User).where(User.is_deleted.is_(False))
            users = session.scalars(stmt).all()
            return list(users)

    def register_user(self, username: str, password: str, role: str) -> User:
        with get_session() as session:
            # Check if user exists
            stmt = select(User).where(User.username == username, User.is_deleted.is_(False))
            existing = session.scalar(stmt)
            if existing:
                raise ValidationError("Username already exists", field="username")
                
            new_user = User(
                username=username,
                password_hash=hash_password(password),
                role=role,
                department="Management" if role == "Owner" else None
            )
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            return new_user

    def get_user_by_username(self, username: str) -> Optional[User]:
        with get_session() as session:
            stmt = select(User).where(User.username == username, User.is_deleted.is_(False))
            return session.scalar(stmt)

    def update_user(self, user_id: str, **kwargs) -> User:
        with get_session() as session:
            user = session.get(User, user_id)
            if not user:
                raise RecordNotFoundError("User", user_id)
                
            for key, value in kwargs.items():
                if key == "password":
                    user.password_hash = hash_password(value)
                elif hasattr(user, key):
                    setattr(user, key, value)
                    
            session.commit()
            session.refresh(user)
            return user

    # ------------------------------------------------------------------
    # Activity Logging
    # ------------------------------------------------------------------

    def log_activity(
        self,
        action: str,
        module: str,
        description: str,
        record_id: Optional[str] = None,
    ) -> None:
        """
        Log a user activity from outside the auth service.

        Convenience method for other services to record actions.
        """
        user = self.current_user
        if user is None:
            return
        with get_session() as session:
            self._log_activity(
                session,
                user_id=user.id,
                action=action,
                module=module,
                description=description,
                record_id=record_id,
            )

    @staticmethod
    def _log_activity(
        session,
        *,
        user_id: Optional[str],
        action: str,
        module: str,
        description: str,
        record_id: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """Internal helper to insert an activity log row."""
        from core.base_model import TimestampMixin

        log = ActivityLog()
        log.user_id = user_id or "system"
        log.action = action
        log.module = module
        log.description = description
        log.record_id = record_id
        log.ip_address = ip_address
        session.add(log)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
auth_service = AuthService()
