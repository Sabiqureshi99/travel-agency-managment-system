from sqlalchemy.orm import Session
from sqlalchemy import select, or_, func
from core.base_repository import BaseRepository
from models.hajj import HajjGroup, HajjPilgrim

class HajjGroupRepository(BaseRepository[HajjGroup]):
    def __init__(self, session: Session):
        super().__init__(HajjGroup, session)

    def search_groups(self, query: str = "", skip: int = 0, limit: int = 50) -> dict:
        stmt = select(self.model_class).where(self.model_class.is_deleted == False)
        if query:
            conditions = []
            for field in ('group_code', 'group_name', 'status'):
                col = getattr(self.model_class, field, None)
                if col is not None:
                    conditions.append(col.ilike(f"%{query}%"))
            if conditions:
                stmt = stmt.where(or_(*conditions))
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.session.scalar(count_stmt) or 0
        stmt = stmt.order_by(self.model_class.year.desc()).offset(skip).limit(limit)
        return {'items': list(self.session.scalars(stmt).all()), 'total': total, 'skip': skip, 'limit': limit}

class HajjPilgrimRepository(BaseRepository[HajjPilgrim]):
    def __init__(self, session: Session):
        super().__init__(HajjPilgrim, session)
