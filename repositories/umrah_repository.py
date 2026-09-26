from sqlalchemy.orm import Session
from sqlalchemy import select, or_, func
from sqlalchemy.orm import joinedload
from core.base_repository import BaseRepository
from models.umrah import UmrahPackageTemplate, UmrahPackagePricing, CustomUmrahBooking, UmrahPilgrim


class UmrahPackageTemplateRepository(BaseRepository[UmrahPackageTemplate]):
    """Repository for UmrahPackageTemplate model operations."""

    def __init__(self, session: Session):
        super().__init__(UmrahPackageTemplate, session)

    def search_templates(self, query: str = "", skip: int = 0, limit: int = 50) -> dict:
        """Search Umrah package templates with pagination."""
        stmt = select(self.model_class).where(self.model_class.is_deleted == False)
        if query:
            conditions = []
            for field in ('name', 'makkah_hotel', 'medinah_hotel'):
                col = getattr(self.model_class, field, None)
                if col is not None:
                    conditions.append(col.ilike(f"%{query}%"))
            if conditions:
                stmt = stmt.where(or_(*conditions))
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.session.scalar(count_stmt) or 0
        stmt = stmt.order_by(self.model_class.created_at.desc()).offset(skip).limit(limit)
        return {'items': list(self.session.scalars(stmt).all()), 'total': total, 'skip': skip, 'limit': limit}


class UmrahPackagePricingRepository(BaseRepository[UmrahPackagePricing]):
    """Repository for UmrahPackagePricing model operations."""

    def __init__(self, session: Session):
        super().__init__(UmrahPackagePricing, session)


class CustomUmrahBookingRepository(BaseRepository[CustomUmrahBooking]):
    """Repository for CustomUmrahBooking model operations."""

    def __init__(self, session: Session):
        super().__init__(CustomUmrahBooking, session)

    def search_bookings(self, query: str = "", skip: int = 0, limit: int = 50) -> dict:
        """Search custom Umrah bookings with pagination."""
        stmt = select(self.model_class).where(self.model_class.is_deleted == False)
        if query:
            conditions = []
            for field in ('booking_number', 'status'):
                col = getattr(self.model_class, field, None)
                if col is not None:
                    conditions.append(col.ilike(f"%{query}%"))
            if conditions:
                stmt = stmt.where(or_(*conditions))
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.session.scalar(count_stmt) or 0
        stmt = stmt.options(joinedload(self.model_class.customer)).order_by(self.model_class.created_at.desc()).offset(skip).limit(limit)
        return {'items': list(self.session.scalars(stmt).all()), 'total': total, 'skip': skip, 'limit': limit}


class UmrahPilgrimRepository(BaseRepository[UmrahPilgrim]):
    """Repository for UmrahPilgrim model operations."""

    def __init__(self, session: Session):
        super().__init__(UmrahPilgrim, session)
