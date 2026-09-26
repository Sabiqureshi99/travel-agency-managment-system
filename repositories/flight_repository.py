from sqlalchemy.orm import Session
from sqlalchemy import select, or_, func
from core.base_repository import BaseRepository
from models.flight import FlightBooking, FlightPassenger

class FlightBookingRepository(BaseRepository[FlightBooking]):
    """Repository for FlightBooking model operations."""
    
    def __init__(self, session: Session):
        super().__init__(FlightBooking, session)
        
    def search_flights(self, query: str = "", fields: list[str] | None = None, skip: int = 0, limit: int = 50) -> dict:
        """
        Search flights with pagination, sorting, and field filtering.
        Returns a dict containing 'items' and 'total'.
        """
        from sqlalchemy.orm import joinedload
        base_stmt = select(self.model_class).where(self.model_class.is_deleted == False)
        
        if query and fields:
            conditions = []
            for field in fields:
                if hasattr(self.model_class, field):
                    column = getattr(self.model_class, field)
                    conditions.append(column.ilike(f"%{query}%"))
            if conditions:
                base_stmt = base_stmt.where(or_(*conditions))
                
        # Get total count before pagination
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total = self.session.scalar(count_stmt) or 0
        
        # Apply ordering and joins
        stmt = base_stmt.options(
            joinedload(self.model_class.customer),
            joinedload(self.model_class.passengers),
            joinedload(self.model_class.segments),
        ).order_by(self.model_class.departure_date.desc()).offset(skip).limit(limit)
        
        items = list(self.session.scalars(stmt).unique().all())
        return {
            'items': items,
            'total': total,
            'skip': skip,
            'limit': limit
        }

    def get_by_id(self, id: str):
        from sqlalchemy.orm import joinedload
        stmt = select(self.model_class).options(
            joinedload(self.model_class.customer),
            joinedload(self.model_class.passengers),
            joinedload(self.model_class.segments),
        ).where(self.model_class.id == id)
        return self.session.scalars(stmt).unique().first()

class FlightPassengerRepository(BaseRepository[FlightPassenger]):
    """Repository for FlightPassenger model operations."""
    def __init__(self, session: Session):
        super().__init__(FlightPassenger, session)
