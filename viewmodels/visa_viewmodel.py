from PySide6.QtCore import Signal
from core.base_viewmodel import BaseViewModel

class VisaViewModel(BaseViewModel):
    """
    ViewModel for the Visa Management module.
    Handles loading, creating, updating, and deleting visas.
    """
    
    visas_loaded = Signal(dict)
    visa_saved = Signal(object)
    visa_deleted = Signal()
    form_data_loaded = Signal(dict)
    
    def __init__(self):
        super().__init__()
        from services.visa_service import VisaService
        self.service = VisaService()
        
    def load_form_data(self):
        """Loads customers in the background for the visa form."""
        self.set_loading(True)
        def _fetch():
            from services.customer_service import CustomerService
            customers = CustomerService().search_customers(limit=1000)
            return {'customers': customers}
            
        self.run_in_thread(
            _fetch,
            on_success=self._on_form_data_success,
            on_error=self._on_form_data_error
        )
        
    def _on_form_data_success(self, result):
        self.set_loading(False)
        self.form_data_loaded.emit(result)
        
    def _on_form_data_error(self, error):
        self.set_loading(False)
        self.show_error(f"Failed to load form data: {error}")
        
    def load_visas(self, query: str = "", skip: int = 0, limit: int = 100):
        """Load visas asynchronously."""
        self.set_loading(True)
        self.run_in_thread(
            lambda: self.service.search_visas(query, fields=['application_number', 'country', 'visa_type', 'status'], skip=skip, limit=limit),
            on_success=self._on_load_success,
            on_error=self._on_load_error
        )
        
    def _on_load_success(self, result):
        self.set_loading(False)
        self.visas_loaded.emit(result)
        
    def _on_load_error(self, error):
        self.set_loading(False)
        self.show_error(f"Failed to load visas: {error}")

    def save_visa(self, application_data: dict, applicants_data: list, current_user_id: str):
        """Create or update a visa application asynchronously."""
        self.set_loading(True)
        self.run_in_thread(
            lambda: self._save_visa_sync(application_data, applicants_data, current_user_id),
            on_success=self._on_save_success,
            on_error=self._on_save_error
        )
        
    def _save_visa_sync(self, application_data: dict, applicants_data: list, current_user_id: str):
        if 'id' in application_data and application_data['id']:
            application_id = application_data.pop('id')
            return self.service.update_application_status(application_id, application_data, updated_by=current_user_id)
        else:
            return self.service.submit_application(application_data, applicants_data, created_by=current_user_id)
            
    def _on_save_success(self, result):
        self.set_loading(False)
        self.show_success("Visa application saved successfully.")
        self.visa_saved.emit(result)
        
    def _on_save_error(self, error):
        self.set_loading(False)
        self.show_error(f"Failed to save visa: {error}")
