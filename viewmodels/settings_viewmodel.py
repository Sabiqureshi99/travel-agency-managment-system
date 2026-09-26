from PySide6.QtCore import QObject, Signal, QThread
from services.company_profile_service import CompanyProfileService
from services.backup_service import BackupService
from services.auth_service import AuthService
from core.base_viewmodel import BaseViewModel

class SettingsViewModel(BaseViewModel):
    config_loaded = Signal(object)
    config_saved = Signal()
    backup_completed = Signal(str)
    backup_failed = Signal(str)
    backup_history_loaded = Signal(list)
    restore_completed = Signal()
    users_loaded = Signal(list)
    user_saved = Signal()

    def __init__(self):
        super().__init__()
        self.profile_service = CompanyProfileService()
        self.backup_service = BackupService()
        self.auth_service = AuthService()

    def load_config(self):
        self.run_in_thread(self.profile_service.get_profile, self.config_loaded.emit)

    def save_config(self, config_data):
        self.run_in_thread(lambda: self.profile_service.save_profile(config_data), lambda _: self.config_saved.emit())

    def load_backup_history(self):
        self.run_in_thread(self.backup_service.get_backup_history, self.backup_history_loaded.emit)

    def create_backup(self):
        def _success(path):
            self.backup_completed.emit(path)
            
        def _error(e):
            self.backup_failed.emit(str(e))
            
        self.run_in_thread(self.backup_service.create_incremental_backup, _success, on_error=_error)

    def create_full_backup(self):
        def _success(path):
            self.backup_completed.emit(path)
            
        def _error(e):
            self.backup_failed.emit(str(e))
            
        self.run_in_thread(self.backup_service.create_full_sqlite_backup, _success, on_error=_error)

    def restore_backup(self, file_path):
        def _success(_):
            self.restore_completed.emit()
            
        def _error(e):
            self.backup_failed.emit(str(e))
            
        self.run_in_thread(lambda: self.backup_service.restore_from_backup(file_path), _success, on_error=_error)

    def load_users(self):
        self.run_in_thread(self.auth_service.get_all_users, self.users_loaded.emit)

    def create_user(self, user_data):
        def _create():
            return self.auth_service.register_user(
                username=user_data['username'],
                password=user_data['password'],
                role=user_data['role']
            )
        self.run_in_thread(_create, lambda _: self.user_saved.emit())

    def reset_password(self, username, new_password):
        def _reset():
            user = self.auth_service.get_user_by_username(username)
            if user:
                return self.auth_service.update_user(user.id, password=new_password)
        self.run_in_thread(_reset, lambda _: self.user_saved.emit())
