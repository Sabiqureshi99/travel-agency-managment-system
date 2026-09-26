from PySide6.QtCore import Signal
from core.base_viewmodel import BaseViewModel

class FlightViewModel(BaseViewModel):
    """
    ViewModel for the Flight Management module.
    Handles loading, creating, updating, and deleting flights.
    """
    
    flights_loaded = Signal(dict)
    flight_saved = Signal(object)
    flight_deleted = Signal()
    
    def __init__(self):
        super().__init__()
        from services.flight_service import FlightService
        self.service = FlightService()
        
    def load_flights(self, query: str = "", skip: int = 0, limit: int = 100):
        """Load flights asynchronously."""
        self.set_loading(True)
        self.run_in_thread(
            lambda: self.service.search_flights(query, fields=['booking_number', 'airline', 'origin', 'destination', 'pnr'], skip=skip, limit=limit),
            on_success=self._on_load_success,
            on_error=self._on_load_error
        )
        
    def _on_load_success(self, result):
        self.set_loading(False)
        self.flights_loaded.emit(result)
        
    def _on_load_error(self, error):
        self.set_loading(False)
        self.show_error(f"Failed to load flights: {error}")

    def save_flight(self, booking_data: dict, passengers_data: list, current_user_id: str):
        """Create or update a flight asynchronously."""
        self.set_loading(True)
        self.run_in_thread(
            lambda: self._save_flight_sync(booking_data, passengers_data, current_user_id),
            on_success=self._on_save_success,
            on_error=self._on_save_error
        )
        
    def _save_flight_sync(self, booking_data: dict, passengers_data: list, current_user_id: str):
        if 'id' in booking_data and booking_data['id']:
            return self.service.update_flight(booking_data['id'], booking_data, passengers_data, current_user_id)
        else:
            return self.service.book_flight(booking_data, passengers_data, current_user_id)
            
    def _on_save_success(self, result):
        self.set_loading(False)
        self.show_success("Flight saved successfully.")
        self.flight_saved.emit(result)
        
    def _on_save_error(self, error):
        self.set_loading(False)
        self.show_error(f"Failed to save flight: {error}")
