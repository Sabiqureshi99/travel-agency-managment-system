from sqlalchemy.orm import Session
from core.base_repository import BaseRepository
from models.customer import Customer, CustomerFamilyMember, CustomerEmergencyContact

class CustomerRepository(BaseRepository[Customer]):
    """Repository for Customer model operations."""
    
    def __init__(self, session: Session):
        """Initialize CustomerRepository with DB session."""
        super().__init__(Customer, session)

    def get_by_id(self, id: str) -> Customer | None:
        from sqlalchemy.orm import joinedload
        from sqlalchemy import select
        stmt = select(self.model_class).options(joinedload(self.model_class.family_members), joinedload(self.model_class.emergency_contacts)).where(self.model_class.id == id)
        return self.session.scalars(stmt).unique().first()

    def get_by_phone(self, phone: str) -> Customer | None:
        """Get a customer by their phone number."""
        return self.get_by_field('phone', phone)

    def get_by_email(self, email: str) -> Customer | None:
        """Get a customer by their email address."""
        return self.get_by_field('email', email)

    def get_all(self, skip: int = 0, limit: int = 100, include_deleted: bool = False):
        from sqlalchemy.orm import joinedload
        from sqlalchemy import select
        stmt = select(self.model_class).options(joinedload(self.model_class.family_members), joinedload(self.model_class.emergency_contacts))
        if not include_deleted:
            stmt = stmt.where(self.model_class.is_deleted == False)
        stmt = stmt.offset(skip).limit(limit)
        return list(self.session.scalars(stmt).unique().all())

    def search(self, query_str: str, fields: list[str], skip: int = 0, limit: int = 100):
        if not fields or not query_str:
            return self.get_all(skip=skip, limit=limit)
        from sqlalchemy.orm import joinedload
        from sqlalchemy import select, or_
        conditions = []
        for field in fields:
            column = getattr(self.model_class, field)
            conditions.append(column.ilike(f"%{query_str}%"))
        stmt = select(self.model_class).options(joinedload(self.model_class.family_members), joinedload(self.model_class.emergency_contacts)).where(or_(*conditions)).where(self.model_class.is_deleted == False).offset(skip).limit(limit)
        return list(self.session.scalars(stmt).unique().all())

class CustomerFamilyMemberRepository(BaseRepository[CustomerFamilyMember]):
    """Repository for CustomerFamilyMember model operations."""
    def __init__(self, session: Session):
        super().__init__(CustomerFamilyMember, session)

class CustomerEmergencyContactRepository(BaseRepository[CustomerEmergencyContact]):
    """Repository for CustomerEmergencyContact model operations."""
    def __init__(self, session: Session):
        super().__init__(CustomerEmergencyContact, session)
