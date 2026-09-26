from sqlalchemy.orm import Session
from sqlalchemy import select
from core.base_repository import BaseRepository
from models.user import User, ActivityLog

class UserRepository(BaseRepository[User]):
    """Repository for User model."""
    
    def __init__(self, session: Session):
        """Initialize UserRepository with DB session."""
        super().__init__(User, session)

    def get_by_username(self, username: str) -> User | None:
        """Get a user by their username."""
        return self.get_by_field('username', username)
        
    def get_by_email(self, email: str) -> User | None:
        """Get a user by their email address."""
        return self.get_by_field('email', email)


class ActivityLogRepository(BaseRepository[ActivityLog]):
    """Repository for ActivityLog model."""
    
    def __init__(self, session: Session):
        """Initialize ActivityLogRepository with DB session."""
        super().__init__(ActivityLog, session)
        
    def get_logs_by_user(self, user_id: str, limit: int = 100) -> list[ActivityLog]:
        """Fetch activity logs for a specific user."""
        stmt = select(ActivityLog).where(ActivityLog.user_id == user_id).order_by(ActivityLog.created_at.desc()).limit(limit)
        return list(self.session.scalars(stmt).all())
