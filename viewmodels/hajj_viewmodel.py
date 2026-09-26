from PySide6.QtCore import Signal
from core.base_viewmodel import BaseViewModel
from services.hajj_service import HajjService

class HajjViewModel(BaseViewModel):
    groups_loaded = Signal(dict)
    group_saved = Signal(object)

    def __init__(self):
        super().__init__()
        self.service = HajjService()

    def load_groups(self, query='', skip=0, limit=100):
        try:
            result = self.service.search_groups(query, skip, limit)
            self.groups_loaded.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))

    def save_group(self, group_data, current_user_id):
        try:
            if 'id' in group_data and group_data['id']:
                result = self.service.update_group(group_data['id'], group_data, current_user_id)
            else:
                result = self.service.create_group(group_data, current_user_id)
            self.group_saved.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))
