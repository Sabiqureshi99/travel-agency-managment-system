from PySide6.QtCore import Signal
from core.base_viewmodel import BaseViewModel

class EmployeeViewModel(BaseViewModel):
    """
    ViewModel for the Employee Management modules.
    Handles loading, creating, updating, and deleting employees.
    """
    
    employees_loaded = Signal(dict)
    employee_saved = Signal(object)
    employee_deleted = Signal()
    
    def __init__(self):
        super().__init__()
        from services.employee_service import EmployeeService
        self.service = EmployeeService()
        
    def load_employees(self, query: str = "", skip: int = 0, limit: int = 100):
        """Load employees asynchronously."""
        self.set_loading(True)
        self.run_in_thread(
            lambda: self.service.search_employees(query, fields=['first_name', 'last_name', 'phone', 'department', 'designation', 'email', 'cnic', 'employee_code'], skip=skip, limit=limit),
            on_success=self._on_load_success,
            on_error=self._on_load_error
        )
        
    def _on_load_success(self, result):
        self.set_loading(False)
        self.employees_loaded.emit(result)
        
    def _on_load_error(self, error):
        self.set_loading(False)
        self.show_error(f"Failed to load employees: {error}")

    def save_employee(self, employee_data: dict, current_user_id: str):
        """Create or update an employee asynchronously."""
        self.set_loading(True)
        self.run_in_thread(
            lambda: self._save_employee_sync(employee_data, current_user_id),
            on_success=self._on_save_success,
            on_error=self._on_save_error
        )
        
    def _save_employee_sync(self, employee_data: dict, current_user_id: str):
        if 'id' in employee_data and employee_data['id']:
            employee_id = employee_data.pop('id')
            return self.service.update_employee(employee_id, employee_data, updated_by=current_user_id)
        else:
            return self.service.create_employee(employee_data, created_by=current_user_id)
            
    def _on_save_success(self, result):
        self.set_loading(False)
        self.show_success("Employee saved successfully.")
        self.employee_saved.emit(result)
        
    def _on_save_error(self, error):
        self.set_loading(False)
        self.show_error(f"Failed to save employee: {error}")

    def delete_employee(self, employee_id: str, current_user_id: str):
        """Soft delete an employee asynchronously."""
        self.set_loading(True)
        self.run_in_thread(
            lambda: self.service.delete_employee(employee_id, deleted_by=current_user_id),
            on_success=self._on_delete_success,
            on_error=self._on_delete_error
        )
        
    def _on_delete_success(self, result):
        self.set_loading(False)
        if result:
            self.show_success("Employee deleted successfully.")
            self.employee_deleted.emit()
        else:
            self.show_error("Failed to delete employee.")
            
    def _on_delete_error(self, error):
        self.set_loading(False)
        self.show_error(f"Failed to delete employee: {error}")
