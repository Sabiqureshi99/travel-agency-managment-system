from PySide6.QtCore import Signal
from core.base_viewmodel import BaseViewModel
from services.umrah_service import UmrahService
from services.customer_service import CustomerService
from services.accounting_service import AccountingService
from services.invoice_generator import InvoiceGenerator
import os
from datetime import date

class UmrahViewModel(BaseViewModel):
    """ViewModel for Umrah Packages and Custom Bookings."""
    
    template_saved = Signal(object)
    # booking_saved = Signal(object)  # Removed unused signal
    pricing_loaded = Signal(list)
    templates_loaded = Signal(dict)
    bookings_loaded = Signal(dict)
    form_data_loaded = Signal(dict) # Contains customers and templates

    def __init__(self):
        super().__init__()
        self.service = UmrahService()
        self.customer_service = CustomerService()

    def load_form_data(self):
        """Loads customers and templates in the background for the booking form."""
        self.set_loading(True)
        def _fetch():
            customers = self.customer_service.search_customers(limit=1000)
            if isinstance(customers, dict):
                customers = customers.get('items', [])
            templates = self.service.search_templates(limit=1000).get('items', [])
            return {'customers': customers, 'templates': templates}
            
        self.run_in_thread(
            _fetch,
            on_success=self._on_form_data_success,
            on_error=self.show_error
        )
        
    def _on_form_data_success(self, result):
        self.set_loading(False)
        self.form_data_loaded.emit(result)

    def save_template(self, template_data: dict, pricing_matrix: list, current_user_id: str):
        self.set_loading(True)
        def _save():
            if 'id' in template_data and template_data['id']:
                return self.service.update_master_template(template_data['id'], template_data, pricing_matrix, current_user_id)
            else:
                return self.service.create_master_template(template_data, pricing_matrix, current_user_id)
                
        self.run_in_thread(
            _save,
            on_success=self._on_template_saved,
            on_error=self.show_error
        )
        
    def _on_template_saved(self, result):
        self.set_loading(False)
        self.show_success("Template saved successfully!")
        self.template_saved.emit(result)

    def delete_template(self, template_id: str, current_user_id: str):
        self.set_loading(True)
        self.run_in_thread(
            lambda: self.service.delete_master_template(template_id, current_user_id),
            on_success=self._on_template_deleted,
            on_error=self.show_error
        )
        
    def _on_template_deleted(self, result):
        self.set_loading(False)
        self.show_success("Template deleted successfully!")
        self.load_templates() # Force refresh

    def save_booking(self, booking_data: dict, pilgrims_data: list, current_user_id: str):
        self.set_loading(True)
        def _save():
            if 'id' in booking_data and booking_data['id']:
                return self.service.update_custom_booking(booking_data['id'], booking_data, current_user_id)
            else:
                return self.service.create_custom_booking(booking_data, pilgrims_data, current_user_id)
                
        self.run_in_thread(
            _save,
            on_success=self._on_booking_saved,
            on_error=self.show_error
        )
        
    def _on_booking_saved(self, result):
        self.set_loading(False)
        self.show_success("Booking saved successfully!")

    def load_template_pricing(self, template_id: str):
        self.set_loading(True)
        self.run_in_thread(
            lambda: self.service.get_pricing_for_template(template_id),
            on_success=self._on_pricing_loaded,
            on_error=self.show_error
        )
        
    def _on_pricing_loaded(self, pricing):
        self.set_loading(False)
        self.pricing_loaded.emit(pricing)

    def load_templates(self, query="", skip=0, limit=50):
        self.set_loading(True)
        self.run_in_thread(
            lambda: self.service.search_templates(query, skip, limit),
            on_success=self._on_templates_loaded,
            on_error=self.show_error
        )
        
    def _on_templates_loaded(self, result):
        self.set_loading(False)
        self.templates_loaded.emit(result)

    def load_bookings(self, query="", skip=0, limit=50):
        self.set_loading(True)
        self.run_in_thread(
            lambda: self.service.search_bookings(query, skip, limit),
            on_success=self._on_bookings_loaded,
            on_error=self.show_error
        )
        
    def _on_bookings_loaded(self, result):
        self.set_loading(False)
        self.bookings_loaded.emit(result)

    def save_umrah_booking_and_invoice(self, booking_data: dict, current_user_id: str):
        self.set_loading(True)
        def _save():
            customer_id = booking_data.get('customer_id')
            if not customer_id:
                raise ValueError("Valid customer_id is required")

            # Extract fields expected by UmrahService
            b_data = {
                'customer_id': customer_id,
                'booking_date': booking_data.get('departure_date', date.today()),
                'base_package_price': booking_data.get('base_package_price', 0),
                'airfare_price': booking_data.get('airfare_price', 0),
                'total_pilgrims': booking_data.get('total_pilgrims', 1),
                
                'flight_details': booking_data.get('flight_details'),
                'visa_details': booking_data.get('visa_details'),
                'hotel_details': booking_data.get('hotel_details'),
                'transport_details': booking_data.get('transport_details'),
                'ziyarat_details': booking_data.get('ziyarat_details'),
                
                'status': 'Confirmed'
            }
            
            booking = self.service.create_custom_booking(b_data, [], current_user_id)
            
            acc_service = AccountingService()
            subtotal = booking_data.get('subtotal', 0)
            service_charges = booking_data.get('service_charges', 0)
            discount = booking_data.get('discount', 0)
            grand_total = booking_data.get('grand_total', 0)
            amount_paid = booking_data.get('amount_paid', 0)
            
            inv_data = {
                'customer_id': customer_id,
                'issue_date': date.today(),
                'due_date': date.today(),
                'reference_type': 'CustomUmrahBooking',
                'reference_id': booking.id,
                'subtotal': subtotal,
                'service_charges': service_charges,
                'discount': discount,
                'total_amount': grand_total,
                'amount_paid': amount_paid,
                'amount_remaining': max(0, grand_total - amount_paid),
                'status': 'Paid' if amount_paid >= grand_total else 'Partial'
            }
            
            items = [{
                'description': f'Umrah Package Booking: {booking.booking_number}',
                'quantity': 1, 
                'unit_price': subtotal, 
                'total_price': subtotal
            }]
            
            invoice = acc_service.create_invoice(inv_data, items, current_user_id)
            
            # Fetch with details (customer, items) to prevent DetachedInstanceError during PDF generation
            invoice_with_details = acc_service.get_invoice_with_details(invoice.id)
            
            os.makedirs("reports/output", exist_ok=True)
            pdf_path = os.path.abspath(f"reports/output/{invoice_with_details.invoice_number}.pdf")
            InvoiceGenerator.generate_invoice_pdf(invoice_with_details, pdf_path)
            
            return pdf_path
            
        self.run_in_thread(
            _save,
            on_success=self._on_booking_invoice_saved,
            on_error=self.show_error
        )
        
    def _on_booking_invoice_saved(self, pdf_path):
        self.set_loading(False)
        self.show_success("Booking and Invoice created!")
        
        if os.name == 'nt':
            os.startfile(pdf_path)
