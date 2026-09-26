from PySide6.QtCore import Signal
from core.base_viewmodel import BaseViewModel
from services.accounting_service import AccountingService
from services.customer_service import CustomerService

class AccountingViewModel(BaseViewModel):
    """
    ViewModel for the Accounting Module.
    Handles Invoices, Receipts, and Expenses.
    """
    
    invoices_loaded = Signal(list, int)
    quotations_loaded = Signal(list, int)  # items, total_count
    receipts_loaded = Signal(list, int)
    expenses_loaded = Signal(list, int)
    cashbook_loaded = Signal(list, int, float)  # transactions, total_count, total_balance
    stats_updated = Signal(dict)
    receipt_created = Signal(object)  # emitted with the new Receipt on success
    
    customer_balances_loaded = Signal(list, int)
    customer_ledger_loaded = Signal(list)
    
    # New signals for async form loading
    form_data_loaded = Signal(list)  # list of customers
    customer_invoices_loaded = Signal(list) # list of unpaid invoices for customer
    
    def __init__(self):
        super().__init__()
        self._service = AccountingService()
        self._customer_service = CustomerService()
        
    def load_invoices(self, query: str = "", skip: int = 0, limit: int = 50):
        self.set_loading(True)
        self.run_in_thread(
            lambda: self._service.search_invoices(query, skip, limit),
            on_success=lambda res: self._on_invoices_success(res),
            on_error=self.show_error
        )
        
    def _on_invoices_success(self, result):
        self.set_loading(False)
        self.invoices_loaded.emit(result['items'], result['total'])
        
    def load_receipts(self, query: str = "", skip: int = 0, limit: int = 50):
        self.set_loading(True)
        self.run_in_thread(
            lambda: self._service.search_receipts(query, skip, limit),
            on_success=lambda res: self._on_receipts_success(res),
            on_error=self.show_error
        )
        
    def _on_receipts_success(self, result):
        self.set_loading(False)
        self.receipts_loaded.emit(result['items'], result['total'])

    def load_stats(self):
        self.run_in_thread(
            self._service.get_dashboard_stats,
            on_success=lambda res: self.stats_updated.emit(res),
            on_error=self.show_error
        )
        
    def load_form_data(self):
        self.set_loading(True)
        self.run_in_thread(
            lambda: self._customer_service.search_customers(""),
            on_success=self._on_form_data_success,
            on_error=self.show_error
        )
        
    def _on_form_data_success(self, customers):
        self.set_loading(False)
        self.form_data_loaded.emit(customers)
        
    def load_customer_invoices(self, customer_id: str):
        self.set_loading(True)
        def fetch_invoices():
            # Get all invoices, filter by customer and status
            invoices = self._service.search_invoices(limit=1000)['items']
            return [inv for inv in invoices if inv.customer_id == customer_id and inv.status in ['Unpaid', 'Partial']]
            
        self.run_in_thread(
            fetch_invoices,
            on_success=self._on_customer_invoices_success,
            on_error=self.show_error
        )
        
    def _on_customer_invoices_success(self, invoices):
        self.set_loading(False)
        self.customer_invoices_loaded.emit(invoices)
        
    def create_invoice(self, invoice_data: dict, items_data: list, user_id: str):
        self.set_loading(True)
        self.run_in_thread(
            lambda: self._service.create_invoice(invoice_data, items_data, user_id),
            on_success=self._on_create_invoice_success,
            on_error=self.show_error
        )
        
    def _on_create_invoice_success(self, invoice):
        self.set_loading(False)
        self.show_success("Invoice created successfully.")
        self.load_invoices()
        self.load_stats()
        
    def create_receipt(self, receipt_data: dict, user_id: str):
        self.set_loading(True)
        def _do_create():
            from services.payment_service import PaymentProcessingService
            with self._service._get_session() as session:
                return PaymentProcessingService.process_customer_receipt(
                    session=session,
                    invoice_id=receipt_data.get("invoice_id"),
                    amount=receipt_data.get("amount"),
                    payment_method=receipt_data.get("payment_method"),
                    notes=receipt_data.get("reference_number", ""),
                    current_user_id=user_id
                )
                
        self.run_in_thread(
            _do_create,
            on_success=self._on_create_receipt_success,
            on_error=self.show_error
        )
        
    def _on_create_receipt_success(self, receipt):
        self.set_loading(False)
        self.receipt_created.emit(receipt)
        self.show_success("Receipt generated successfully.")
        self.load_receipts()
        self.load_stats()

    def load_cashbook(self, query: str = "", skip: int = 0, limit: int = 50):
        self.set_loading(True)
        self.run_in_thread(
            lambda: self._service.get_cashbook_ledger(query, skip, limit),
            on_success=self._on_cashbook_success,
            on_error=self.show_error
        )
        
    def _on_cashbook_success(self, result):
        self.set_loading(False)
        self.cashbook_loaded.emit(result['items'], result['total'], result['total_balance'])

    def load_customer_balances(self, query: str = "", skip: int = 0, limit: int = 50):
        self.set_loading(True)
        self.run_in_thread(
            lambda: self._service.get_customer_balances(query, skip, limit),
            on_success=self._on_customer_balances_success,
            on_error=self.show_error
        )
        
    def _on_customer_balances_success(self, result):
        self.set_loading(False)
        self.customer_balances_loaded.emit(result['items'], result['total'])

    def load_customer_ledger(self, customer_id: str):
        self.set_loading(True)
        self.run_in_thread(
            lambda: self._service.get_customer_ledger(customer_id),
            on_success=self._on_customer_ledger_success,
            on_error=self.show_error
        )
        
    def _on_customer_ledger_success(self, ledger):
        self.set_loading(False)
        self.customer_ledger_loaded.emit(ledger)

    def load_quotations(self, query: str = "", skip: int = 0, limit: int = 50):
        self.set_loading(True)
        self.run_in_thread(
            lambda: self._service.search_quotations(query, skip, limit),
            on_success=lambda res: self._on_quotations_success(res),
            on_error=self.show_error
        )
    def _on_quotations_success(self, result):
        self.set_loading(False)
        self.quotations_loaded.emit(result['items'], result['total'])
