from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QComboBox, QPushButton, QFormLayout, 
                               QDateEdit, QDoubleSpinBox, QMessageBox)
from PySide6.QtCore import QDate, Qt

class ReceiptForm(QDialog):
    def __init__(self, viewmodel, current_user_id, parent=None):
        super().__init__(parent)
        self.viewmodel = viewmodel
        self.current_user_id = current_user_id
        self.setWindowTitle("Receive Payment")
        self.setMinimumWidth(400)
        self._save_signals_connected = False  # guard against spurious disconnect warnings
        self._setup_ui()
        self._connect_signals()
        
        # Trigger async load
        self.cmb_customer.addItem("Loading customers...", None)
        self.cmb_customer.setEnabled(False)
        self.viewmodel.load_form_data()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("Receive Payment")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #FFFFFF; margin-bottom: 10px;")
        layout.addWidget(title)
        
        form = QFormLayout()
        form.setSpacing(15)
        
        self.cmb_customer = QComboBox()
        self.cmb_customer.currentIndexChanged.connect(self._on_customer_changed)
        
        self.cmb_invoice = QComboBox()
        self.dt_receipt = QDateEdit(QDate.currentDate())
        self.dt_receipt.setCalendarPopup(True)
        
        self.sp_amount = QDoubleSpinBox()
        self.sp_amount.setRange(0.01, 999999999)
        self.sp_amount.setPrefix("Rs. ")
        
        self.cmb_method = QComboBox()
        self.cmb_method.addItems(["Cash", "Bank Transfer", "Cheque", "Credit Card"])
        
        self.txt_reference = QLineEdit()
        self.txt_reference.setPlaceholderText("e.g. Check # or Transaction ID")
        
        form.addRow("Customer:", self.cmb_customer)
        form.addRow("Apply to Invoice:", self.cmb_invoice)
        form.addRow("Date:", self.dt_receipt)
        form.addRow("Amount Received:", self.sp_amount)
        form.addRow("Payment Method:", self.cmb_method)
        form.addRow("Reference:", self.txt_reference)
        
        layout.addLayout(form)
        
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Save Receipt")
        btn_save.setDefault(True)
        btn_save.setShortcut("Return")
        btn_save.setObjectName("btn_success")
        btn_cancel = QPushButton("Cancel")
        
        btn_save.clicked.connect(self._save)
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)
        
    def _connect_signals(self):
        self.viewmodel.form_data_loaded.connect(self._on_customers_loaded)
        self.viewmodel.customer_invoices_loaded.connect(self._on_invoices_loaded)
        
    def _on_customers_loaded(self, customers):
        self.cmb_customer.blockSignals(True)
        self.cmb_customer.clear()
        self.cmb_customer.addItem("-- Select Customer --", None)
        for c in customers:
            self.cmb_customer.addItem(c.full_name, c.id)
        self.cmb_customer.blockSignals(False)
        self.cmb_customer.setEnabled(True)
        
    def _on_customer_changed(self):
        customer_id = self.cmb_customer.currentData()
        self.cmb_invoice.clear()
        self.cmb_invoice.addItem("-- Advance Payment (No Invoice) --", None)
        if not customer_id:
            return
            
        self.cmb_invoice.addItem("Loading invoices...", None)
        self.cmb_invoice.setEnabled(False)
        self.viewmodel.load_customer_invoices(customer_id)
        
    def _on_invoices_loaded(self, invoices):
        self.cmb_invoice.clear()
        self.cmb_invoice.addItem("-- Advance Payment (No Invoice) --", None)
        for inv in invoices:
            self.cmb_invoice.addItem(f"{inv.invoice_number} (Bal: Rs. {inv.amount_remaining:,.2f})", inv.id)
        self.cmb_invoice.setEnabled(True)
        
    def _save(self):
        customer_id = self.cmb_customer.currentData()
        if not customer_id:
            QMessageBox.warning(self, "Validation Error", "Please select a customer.")
            return

        invoice_id = self.cmb_invoice.currentData()
        if not invoice_id:
            QMessageBox.warning(self, "Validation Error",
                                "Please select an invoice to apply this payment to.\n"
                                "Advance payments without an invoice are not yet supported.")
            return

        amount = self.sp_amount.value()
        if amount <= 0:
            QMessageBox.warning(self, "Validation Error", "Amount must be greater than zero.")
            return

        receipt_data = {
            "customer_id": customer_id,
            "invoice_id": invoice_id,
            "receipt_date": self.dt_receipt.date().toPython(),
            "amount": amount,
            "payment_method": self.cmb_method.currentText(),
            "reference_number": self.txt_reference.text(),
        }

        # Disconnect previous one-shot save signals only if they were connected
        if self._save_signals_connected:
            self.viewmodel.receipt_created.disconnect(self._on_save_success)
            self.viewmodel.error_occurred.disconnect(self._on_save_error)

        self.viewmodel.receipt_created.connect(self._on_save_success)
        self.viewmodel.error_occurred.connect(self._on_save_error)
        self._save_signals_connected = True

        self.viewmodel.create_receipt(receipt_data, self.current_user_id)

    def _on_save_success(self, _=None):
        self.accept()

    def _on_save_error(self, message: str):
        QMessageBox.critical(self, "Payment Failed", message)
