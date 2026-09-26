from typing import Any
from contextlib import contextmanager
import logging

from config.database import get_session
from core.exceptions import ValidationError, DuplicateRecordError

class BaseService:
    """Base Service class providing common business logic utilities."""

    def __init__(self):
        """Initialize the service with a logger."""
        self.logger = logging.getLogger(self.__class__.__name__)

    @contextmanager
    def _get_session(self):
        """Context manager to provide a database session."""
        with get_session() as session:
            yield session

    def validate_required(self, data: dict, fields: list[str]) -> None:
        """Validate that all required fields are present and not empty."""
        missing = []
        for field in fields:
            val = data.get(field)
            if val is None or (isinstance(val, str) and not val.strip()):
                missing.append(field)
        if missing:
            raise ValidationError(f"Missing or empty required fields: {', '.join(missing)}")

    def validate_unique(self, session: Any, model_class: type, field: str, value: Any, exclude_id: str | None = None) -> None:
        """Validate that a field value is unique across the database table (ignoring soft-deleted records)."""
        from sqlalchemy import select, func
        stmt = select(func.count()).select_from(model_class).where(getattr(model_class, field) == value)
        
        if hasattr(model_class, 'is_deleted'):
            stmt = stmt.where(model_class.is_deleted == False)
            
        if exclude_id:
            stmt = stmt.where(model_class.id != exclude_id)
            
        count = session.scalar(stmt) or 0
        if count > 0:
            raise DuplicateRecordError(f"{model_class.__name__} with {field}='{value}' already exists.")

    def paginate(self, items: list, page: int = 1, per_page: int = 50) -> dict:
        """Paginate a list of items."""
        total = len(items)
        total_pages = (total + per_page - 1) // per_page
        start = (page - 1) * per_page
        end = start + per_page
        return {
            'items': items[start:end],
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages
        }
