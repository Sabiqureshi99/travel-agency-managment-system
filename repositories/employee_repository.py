from sqlalchemy.orm import Session
from core.base_repository import BaseRepository
from models.employee import Employee, Attendance, SalaryRecord

class EmployeeRepository(BaseRepository[Employee]):
    """Repository for Employee model operations."""
    
    def __init__(self, session: Session):
        """Initialize EmployeeRepository with DB session."""
        super().__init__(Employee, session)

    def get_by_email(self, email: str) -> Employee | None:
        """Get an employee by email."""
        return self.get_by_field('email', email)
        
    def search_employees(self, query: str = "", fields: list[str] | None = None, skip: int = 0, limit: int = 50):
        """
        Search employees with pagination, sorting, and field filtering.
        Returns a dict containing 'items' and 'total'.
        """
        from sqlalchemy import select, or_, func
        from sqlalchemy.orm import joinedload
        
        stmt = select(self.model_class).where(self.model_class.is_deleted == False)
        
        if query and fields:
            conditions = []
            for field in fields:
                if hasattr(self.model_class, field):
                    column = getattr(self.model_class, field)
                    conditions.append(column.ilike(f"%{query}%"))
            if conditions:
                stmt = stmt.where(or_(*conditions))
                
        # Get total count before pagination
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.session.scalar(count_stmt) or 0
        
        # Apply ordering and pagination
        stmt = stmt.options(joinedload(self.model_class.user)).order_by(self.model_class.first_name.asc(), self.model_class.last_name.asc())
        stmt = stmt.offset(skip).limit(limit)
        
        items = list(self.session.scalars(stmt).all())
        return {
            'items': items,
            'total': total,
            'skip': skip,
            'limit': limit
        }

class AttendanceRepository(BaseRepository[Attendance]):
    """Repository for Attendance model operations."""
    def __init__(self, session: Session):
        super().__init__(Attendance, session)

class SalaryRecordRepository(BaseRepository[SalaryRecord]):
    """Repository for SalaryRecord model operations."""
    def __init__(self, session: Session):
        super().__init__(SalaryRecord, session)
