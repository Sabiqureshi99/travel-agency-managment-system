import logging
from typing import Optional
from core.base_service import BaseService
from models.hajj import HajjGroup, HajjPilgrim
from repositories.hajj_repository import HajjGroupRepository, HajjPilgrimRepository
from core.base_model import generate_uuid

logger = logging.getLogger(__name__)


class HajjService(BaseService):
    """Service for managing Hajj groups and pilgrims."""

    def search_groups(self, query: str = "", skip: int = 0, limit: int = 50) -> dict:
        with self._get_session() as session:
            return HajjGroupRepository(session).search_groups(query, skip, limit)

    def create_group(self, group_data: dict, created_by: Optional[str] = None) -> HajjGroup:
        self.validate_required(group_data, ['group_name', 'year'])
        with self._get_session() as session:
            repo = HajjGroupRepository(session)
            count = repo.get_count()
            group_data.setdefault('group_code', f"HAJ-{count + 1:04d}")
            group = HajjGroup(id=generate_uuid(), created_by=created_by)
            for k, v in group_data.items():
                if hasattr(group, k):
                    setattr(group, k, v)
            session.add(group)
            session.commit()
            session.refresh(group)
            logger.info(f"Created Hajj group: {group.group_code}")
            return group

    def get_group(self, group_id: str) -> Optional[HajjGroup]:
        with self._get_session() as session:
            return HajjGroupRepository(session).get_by_id(group_id)

    def update_group(self, group_id: str, group_data: dict, updated_by: Optional[str] = None) -> Optional[HajjGroup]:
        with self._get_session() as session:
            repo = HajjGroupRepository(session)
            group = repo.get_by_id(group_id)
            if not group:
                raise ValueError(f"Hajj group {group_id} not found.")
            for k, v in group_data.items():
                if hasattr(group, k) and k not in ('id', 'created_at', 'created_by', 'group_code'):
                    setattr(group, k, v)
            group.updated_by = updated_by
            session.commit()
            session.refresh(group)
            return group

    def delete_group(self, group_id: str, deleted_by: Optional[str] = None) -> bool:
        with self._get_session() as session:
            repo = HajjGroupRepository(session)
            group = repo.get_by_id(group_id)
            if not group:
                raise ValueError(f"Hajj group {group_id} not found.")
            repo.soft_delete(group, deleted_by=deleted_by or "system")
            session.commit()
            return True

    def create_pilgrim(self, group_id: str, pilgrim_data: dict, created_by: Optional[str] = None) -> HajjPilgrim:
        self.validate_required(pilgrim_data, ['full_name', 'passport_number', 'gender'])
        with self._get_session() as session:
            pilgrim_data['group_id'] = group_id
            pilgrim = HajjPilgrim(id=generate_uuid(), created_by=created_by)
            for k, v in pilgrim_data.items():
                if hasattr(pilgrim, k):
                    setattr(pilgrim, k, v)
            session.add(pilgrim)
            session.commit()
            session.refresh(pilgrim)
            return pilgrim
