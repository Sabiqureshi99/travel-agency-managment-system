from PySide6.QtCore import Signal
from core.base_viewmodel import BaseViewModel
from services.hotel_service import HotelService
from services.customer_service import CustomerService

class HotelViewModel(BaseViewModel):
    hotels_loaded = Signal(dict)
    hotel_bookings_loaded = Signal(dict)
    hotel_saved = Signal(object)
    booking_saved = Signal(object)
    form_data_loaded = Signal(dict)

    def __init__(self):
        super().__init__()
        self.service = HotelService()
        self.customer_service = CustomerService()

    def load_hotels(self, query='', skip=0, limit=100):
        self.set_loading(True)
        def _fetch():
            return self.service.search_hotels(query, skip, limit)
        self.run_in_thread(_fetch, on_success=self._on_hotels_success, on_error=self.show_error)

    def _on_hotels_success(self, result):
        self.set_loading(False)
        self.hotels_loaded.emit(result)

    def load_bookings(self, query='', skip=0, limit=100):
        self.set_loading(True)
        def _fetch():
            return self.service.search_hotel_bookings(query, skip, limit)
        self.run_in_thread(_fetch, on_success=self._on_bookings_success, on_error=self.show_error)

    def _on_bookings_success(self, result):
        self.set_loading(False)
        self.hotel_bookings_loaded.emit(result)

    def load_form_data(self):
        """Loads customers and hotels asynchronously for the booking form dropdowns."""
        self.set_loading(True)
        def _fetch():
            customers = self.customer_service.search_customers(limit=1000)
            if isinstance(customers, dict):
                customers = customers.get('items', [])
            hotels = self.service.search_hotels(limit=1000).get('items', [])
            return {'customers': customers, 'hotels': hotels}
        
        self.run_in_thread(_fetch, on_success=self._on_form_data_success, on_error=self.show_error)

    def _on_form_data_success(self, result):
        self.set_loading(False)
        self.form_data_loaded.emit(result)

    def save_hotel(self, hotel_data, current_user_id):
        self.set_loading(True)
        def _save():
            if 'id' in hotel_data and hotel_data['id']:
                return self.service.update_hotel(hotel_data['id'], hotel_data, current_user_id)
            else:
                return self.service.create_hotel(hotel_data, current_user_id)
        self.run_in_thread(_save, on_success=self._on_hotel_saved, on_error=self.show_error)
        
    def _on_hotel_saved(self, result):
        self.set_loading(False)
        self.show_success("Hotel saved successfully!")
        self.hotel_saved.emit(result)

    def save_booking(self, booking_data, current_user_id):
        self.set_loading(True)
        def _save():
            if 'id' in booking_data and booking_data['id']:
                return self.service.update_hotel_booking(booking_data['id'], booking_data, current_user_id)
            else:
                return self.service.create_hotel_booking(booking_data, current_user_id)
        self.run_in_thread(_save, on_success=self._on_booking_saved, on_error=self.show_error)

    def _on_booking_saved(self, result):
        self.set_loading(False)
        self.show_success("Hotel booking saved successfully!")
        self.booking_saved.emit(result)

