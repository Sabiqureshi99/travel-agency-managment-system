from PySide6.QtCore import Signal
from core.base_viewmodel import BaseViewModel

class CustomerViewModel(BaseViewModel):
    """
    ViewModel for the Customer Management modules.
    Handles loading, creating, updating, and deleting customers.
    """
    
    customers_loaded = Signal(list, int)
    customer_saved = Signal(object)
    customer_deleted = Signal()
    
    def __init__(self):
        super().__init__()
        from services.customer_service import CustomerService
        self.service = CustomerService()
        
    def load_customers(self, query: str = "", skip: int = 0, limit: int = 100):
        """Load customers asynchronously."""
        self.set_loading(True)
        self.run_in_thread(
            lambda: self.service.search_customers_paginated(query, fields=['first_name', 'last_name', 'phone_primary', 'cnic', 'passport_number'], skip=skip, limit=limit),
            on_success=self._on_load_success,
            on_error=self._on_load_error
        )
        
    def _on_load_success(self, result):
        self.set_loading(False)
        data, total = result
        self.customers_loaded.emit(data, total)
        
    def _on_load_error(self, error):
        self.set_loading(False)
        self.show_error(f"Failed to load customers: {error}")

    def save_customer(self, customer_data: dict, current_user_id: str):
        """Create or update a customer asynchronously."""
        self.set_loading(True)
        self.run_in_thread(
            lambda: self._save_customer_sync(customer_data, current_user_id),
            on_success=self._on_save_success,
            on_error=self._on_save_error
        )
        
    def _save_customer_sync(self, customer_data: dict, current_user_id: str):
        if 'id' in customer_data and customer_data['id']:
            customer_id = customer_data.pop('id')
            return self.service.update_customer(customer_id, customer_data, updated_by=current_user_id)
        else:
            return self.service.create_customer(customer_data, created_by=current_user_id)
            
    def _on_save_success(self, result):
        self.set_loading(False)
        self.show_success("Customer saved successfully.")
        self.customer_saved.emit(result)
        
    def _on_save_error(self, error):
        self.set_loading(False)
        self.show_error(f"Failed to save customer: {error}")

    def delete_customer(self, customer_id: str, current_user_id: str):
        """Soft delete a customer asynchronously."""
        self.set_loading(True)
        self.run_in_thread(
            lambda: self.service.delete_customer(customer_id, deleted_by=current_user_id),
            on_success=self._on_delete_success,
            on_error=self._on_delete_error
        )
        
    def _on_delete_success(self, result):
        self.set_loading(False)
        if result:
            self.show_success("Customer deleted successfully.")
            self.customer_deleted.emit()
        else:
            self.show_error("Failed to delete customer.")
            
    def _on_delete_error(self, error):
        self.set_loading(False)
        self.show_error(f"Failed to delete customer: {error}")
