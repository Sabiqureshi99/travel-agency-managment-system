from sqlalchemy.orm import Session
from sqlalchemy import select, or_, func
from sqlalchemy.orm import joinedload
from core.base_repository import BaseRepository
from models.hotel import Hotel, HotelBooking


class HotelRepository(BaseRepository[Hotel]):
    """Repository for Hotel model operations."""

    def __init__(self, session: Session):
        super().__init__(Hotel, session)

    def search_hotels(self, query: str = "", skip: int = 0, limit: int = 50) -> dict:
        """Search hotels with pagination and text filtering."""
        stmt = select(self.model_class).where(self.model_class.is_deleted == False)
        if query:
            conditions = []
            for field in ('hotel_name', 'hotel_code', 'city', 'country'):
                col = getattr(self.model_class, field, None)
                if col is not None:
                    conditions.append(col.ilike(f"%{query}%"))
            if conditions:
                stmt = stmt.where(or_(*conditions))
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.session.scalar(count_stmt) or 0
        stmt = stmt.order_by(self.model_class.hotel_name.asc()).offset(skip).limit(limit)
        return {'items': list(self.session.scalars(stmt).all()), 'total': total, 'skip': skip, 'limit': limit}


class HotelBookingRepository(BaseRepository[HotelBooking]):
    """Repository for HotelBooking operations."""

    def __init__(self, session: Session):
        super().__init__(HotelBooking, session)

    def search_hotel_bookings(self, query: str = "", skip: int = 0, limit: int = 50) -> dict:
        """Search hotel bookings with pagination and text filtering."""
        base_stmt = select(self.model_class).where(self.model_class.is_deleted == False)
        if query:
            conditions = []
            for field in ('booking_number', 'status', 'voucher_number'):
                col = getattr(self.model_class, field, None)
                if col is not None:
                    conditions.append(col.ilike(f"%{query}%"))
            if conditions:
                base_stmt = base_stmt.where(or_(*conditions))
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total = self.session.scalar(count_stmt) or 0
        stmt = base_stmt.options(
            joinedload(self.model_class.hotel),
            joinedload(self.model_class.customer)
        ).order_by(self.model_class.check_in_date.desc()).offset(skip).limit(limit)
        return {'items': list(self.session.scalars(stmt).all()), 'total': total, 'skip': skip, 'limit': limit}
