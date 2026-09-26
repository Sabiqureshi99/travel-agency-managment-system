from typing import Generic, TypeVar, Any, Sequence
from sqlalchemy.orm import Session
from sqlalchemy import select, update as sql_update, func
from core.base_model import BaseModel

T = TypeVar('T', bound=BaseModel)

class BaseRepository(Generic[T]):
    """Generic Repository for database operations."""

    def __init__(self, model_class: type[T], session: Session):
        """Initialize with model class and database session."""
        self.model_class = model_class
        self.session = session

    def get_by_id(self, id: str) -> T | None:
        """Fetch an entity by its ID."""
        return self.session.get(self.model_class, id)

    def get_all(self, skip: int = 0, limit: int = 100, include_deleted: bool = False) -> list[T]:
        """Fetch all entities with optional pagination and soft-delete filtering."""
        stmt = select(self.model_class).offset(skip).limit(limit)
        if hasattr(self.model_class, 'is_deleted') and not include_deleted:
            stmt = stmt.where(self.model_class.is_deleted == False)
        return list(self.session.scalars(stmt).all())

    def get_count(self, include_deleted: bool = False) -> int:
        """Get total count of entities."""
        stmt = select(func.count()).select_from(self.model_class)
        if hasattr(self.model_class, 'is_deleted') and not include_deleted:
            stmt = stmt.where(self.model_class.is_deleted == False)
        return self.session.scalar(stmt) or 0

    def add(self, entity: T) -> T:
        """Add a new entity to the database."""
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def update(self, entity: T) -> T:
        """Update an existing entity."""
        self.session.merge(entity)
        self.session.commit()
        return entity

    def soft_delete(self, entity: T, deleted_by: str) -> T:
        """Soft delete an entity by setting is_deleted flag."""
        if hasattr(entity, 'is_deleted'):
            entity.is_deleted = True # type: ignore
            if hasattr(entity, 'deleted_by'):
                entity.deleted_by = deleted_by # type: ignore
            self.session.commit()
        return entity

    def hard_delete(self, entity: T) -> None:
        """Permanently delete an entity from the database."""
        self.session.delete(entity)
        self.session.commit()

    def search(self, query_str: str, fields: list[str], skip: int = 0, limit: int = 100) -> list[T]:
        """Search entities by a query string across specified fields."""
        if not fields or not query_str:
            return self.get_all(skip=skip, limit=limit)
        
        conditions = []
        for field in fields:
            column = getattr(self.model_class, field)
            conditions.append(column.ilike(f"%{query_str}%"))
            
        from sqlalchemy import or_
        stmt = select(self.model_class).where(or_(*conditions)).offset(skip).limit(limit)
        return list(self.session.scalars(stmt).all())

    def get_all_paginated(self, skip: int = 0, limit: int = 100, include_deleted: bool = False) -> tuple[list[T], int]:
        """Fetch all entities with pagination and return (data, total_count)."""
        stmt = select(self.model_class)
        count_stmt = select(func.count()).select_from(self.model_class)
        
        if hasattr(self.model_class, 'is_deleted') and not include_deleted:
            stmt = stmt.where(self.model_class.is_deleted == False)
            count_stmt = count_stmt.where(self.model_class.is_deleted == False)
            
        total = self.session.scalar(count_stmt) or 0
        data = list(self.session.scalars(stmt.offset(skip).limit(limit)).all())
        return data, total

    def search_paginated(self, query_str: str, fields: list[str], skip: int = 0, limit: int = 100) -> tuple[list[T], int]:
        """Search entities by a query string across specified fields and return (data, total_count)."""
        if not fields or not query_str:
            return self.get_all_paginated(skip=skip, limit=limit)
        
        conditions = []
        for field in fields:
            column = getattr(self.model_class, field)
            conditions.append(column.ilike(f"%{query_str}%"))
            
        from sqlalchemy import or_
        base_stmt = select(self.model_class).where(or_(*conditions))
        
        # Build count query
        count_stmt = select(func.count()).select_from(self.model_class).where(or_(*conditions))
        
        # If soft delete is supported, filter out deleted records
        if hasattr(self.model_class, 'is_deleted'):
            base_stmt = base_stmt.where(self.model_class.is_deleted == False)
            count_stmt = count_stmt.where(self.model_class.is_deleted == False)

        total = self.session.scalar(count_stmt) or 0
        data = list(self.session.scalars(base_stmt.offset(skip).limit(limit)).all())
        return data, total

    def get_by_field(self, field_name: str, value: Any) -> T | None:
        """Get a single entity by a specific field value."""
        stmt = select(self.model_class).where(getattr(self.model_class, field_name) == value)
        return self.session.scalars(stmt).first()

    def get_all_by_field(self, field_name: str, value: Any) -> list[T]:
        """Get all entities matching a specific field value."""
        stmt = select(self.model_class).where(getattr(self.model_class, field_name) == value)
        return list(self.session.scalars(stmt).all())

    def exists(self, field_name: str, value: Any, exclude_id: str | None = None) -> bool:
        """Check if an entity exists with a specific field value."""
        stmt = select(func.count()).select_from(self.model_class).where(getattr(self.model_class, field_name) == value)
        if exclude_id:
            stmt = stmt.where(self.model_class.id != exclude_id)
        return (self.session.scalar(stmt) or 0) > 0

    def bulk_add(self, entities: list[T]) -> list[T]:
        """Add multiple entities to the database in one transaction."""
        self.session.add_all(entities)
        self.session.commit()
        for entity in entities:
            self.session.refresh(entity)
        return entities
