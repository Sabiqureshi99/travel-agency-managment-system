from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit, QFormLayout, QComboBox, QMessageBox, QScrollArea, QFrame
, QAbstractItemView)
from PySide6.QtCore import Qt
from services.accounting_service import AccountingService

class InvoiceDetailsDialog(QDialog):
    def __init__(self, invoice_id: str, parent=None):
        super().__init__(parent)
        self.invoice_id = invoice_id
        self.acc_service = AccountingService()
        
        self.setWindowTitle("Invoice & Payment Ledger")
        self.setMinimumSize(1000, 600)
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- LEFT SIDE (Invoice Details) ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(20, 20, 20, 20)
        left_layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        self.lbl_inv_number = QLabel("Invoice: Loading...")
        self.lbl_inv_number.setObjectName("lbl_title")
        self.lbl_status = QLabel("STATUS")
        self.lbl_status.setStyleSheet("background-color: #2D3748; padding: 5px 10px; border-radius: 5px; font-weight: bold;")
        
        header_layout.addWidget(self.lbl_inv_number)
        header_layout.addStretch()
        header_layout.addWidget(self.lbl_status)
        left_layout.addLayout(header_layout)
        
        self.lbl_customer = QLabel("Passenger Name: Loading...\nPassport No: Loading...")
        left_layout.addWidget(self.lbl_customer)
        
        # Items Table
        self.items_table = QTableWidget(0, 4)
        self.items_table.setHorizontalHeaderLabels(["Description", "Qty", "Unit Price", "Total"])
        hdr = self.items_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.Interactive)
        hdr.setSectionResizeMode(3, QHeaderView.Interactive)
        self.items_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        left_layout.addWidget(self.items_table)
        
        # Totals
        totals_layout = QVBoxLayout()
        totals_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.lbl_total = QLabel("Total Amount: 0.00")
        self.lbl_paid = QLabel("Amount Paid: 0.00")
        self.lbl_balance = QLabel("Balance Due: 0.00")
        
        for lbl in [self.lbl_total, self.lbl_paid, self.lbl_balance]:
            lbl.setStyleSheet("font-size: 14px; font-weight: bold;")
            totals_layout.addWidget(lbl)
            
        left_layout.addLayout(totals_layout)
        
        # --- RIGHT SIDE (Payment Ledger) ---
        right_widget = QWidget()
        right_widget.setObjectName("sidebar")
        right_widget.setFixedWidth(350)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(20)
        
        right_layout.addWidget(QLabel("<b>Payment Ledger</b>", styleSheet="font-size: 16px;"))
        
        # Payment Form
        form_frame = QFrame()
        form_frame.setStyleSheet("background-color: #1E293B; border-radius: 8px; padding: 10px;")
        form_layout = QFormLayout(form_frame)
        
        self.inp_amount = QLineEdit()
        self.inp_amount.setPlaceholderText("Enter Amount...")
        self.inp_amount.setMinimumHeight(35)
        
        self.cb_method = QComboBox()
        self.cb_method.addItems(["Cash", "Bank Transfer", "Cheque", "Credit Card"])
        self.cb_method.setMinimumHeight(35)
        
        self.inp_ref = QLineEdit()
        self.inp_ref.setPlaceholderText("Reference # (Optional)")
        self.inp_ref.setMinimumHeight(35)
        
        btn_pay = QPushButton("Receive Payment")
        btn_pay.setObjectName("btn_primary")
        btn_pay.setShortcut("Return")
        btn_pay.setMinimumHeight(40)
        btn_pay.clicked.connect(self.process_payment)
        
        form_layout.addRow("Amount:", self.inp_amount)
        form_layout.addRow("Method:", self.cb_method)
        form_layout.addRow("Ref:", self.inp_ref)
        form_layout.addRow(btn_pay)
        
        right_layout.addWidget(form_frame)
        
        # History Table
        right_layout.addWidget(QLabel("<b>Transaction History</b>"))
        self.history_table = QTableWidget(0, 3)
        self.history_table.setHorizontalHeaderLabels(["Date", "Method", "Amount"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        right_layout.addWidget(self.history_table)
        
        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget)
        
    def load_data(self):
        invoice = self.acc_service.get_invoice_with_details(self.invoice_id)
        if not invoice:
            QMessageBox.critical(self, "Error", "Invoice not found.")
            self.close()
            return
            
        self.lbl_inv_number.setText(f"Invoice: {invoice.invoice_number}")
        customer_name = invoice.customer.full_name if invoice.customer else "CASH CUSTOMER"
        passport = invoice.customer.passport_number if (invoice.customer and invoice.customer.passport_number) else "N/A"
        self.lbl_customer.setText(f"Passenger Name: {customer_name}\nPassport No: {passport}")
        self.lbl_status.setText(invoice.status.upper())
        
        if invoice.status.lower() == "paid":
            self.lbl_status.setStyleSheet("background-color: #38A169; padding: 5px 10px; border-radius: 5px; font-weight: bold; color: white;")
        elif invoice.status.lower() == "partial":
            self.lbl_status.setStyleSheet("background-color: #D69E2E; padding: 5px 10px; border-radius: 5px; font-weight: bold; color: white;")
        else:
            self.lbl_status.setStyleSheet("background-color: #E53E3E; padding: 5px 10px; border-radius: 5px; font-weight: bold; color: white;")
            
        self.lbl_total.setText(f"Total Amount: PKR {invoice.total_amount:,.2f}")
        self.lbl_paid.setText(f"Amount Paid: PKR {invoice.amount_paid:,.2f}")
        self.lbl_balance.setText(f"Balance Due: PKR {invoice.amount_remaining:,.2f}")
        
        self.inp_amount.setText(str(invoice.amount_remaining))
        
        # Disable payment if fully paid
        if float(invoice.amount_remaining) <= 0:
            self.inp_amount.setEnabled(False)
            self.cb_method.setEnabled(False)
            self.inp_ref.setEnabled(False)
            
        # Load items
        self.items_table.setRowCount(0)
        for i, item in enumerate(invoice.items):
            self.items_table.insertRow(i)
            self.items_table.setItem(i, 0, QTableWidgetItem(item.description))
            self.items_table.setItem(i, 1, QTableWidgetItem(str(item.quantity)))
            self.items_table.setItem(i, 2, QTableWidgetItem(f"{item.unit_price:,.2f}"))
            self.items_table.setItem(i, 3, QTableWidgetItem(f"{item.total_price:,.2f}"))
            
        # Load history
        self.history_table.setRowCount(0)
        for i, pt in enumerate(invoice.payment_transactions):
            self.history_table.insertRow(i)
            self.history_table.setItem(i, 0, QTableWidgetItem(str(pt.payment_date)))
            self.history_table.setItem(i, 1, QTableWidgetItem(pt.payment_method))
            self.history_table.setItem(i, 2, QTableWidgetItem(f"{pt.amount:,.2f}"))

    def process_payment(self):
        try:
            amount = float(self.inp_amount.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid Amount", "Please enter a valid numeric amount.")
            return
            
        if amount <= 0:
            QMessageBox.warning(self, "Invalid Amount", "Amount must be greater than 0.")
            return
            
        method = self.cb_method.currentText()
        ref = self.inp_ref.text()
        
        success = self.acc_service.add_payment_transaction(
            self.invoice_id, amount, method, ref, "SYSTEM"
        )
        
        if success:
            QMessageBox.information(self, "Success", "Payment recorded successfully!")
            self.load_data()
        else:
            QMessageBox.critical(self, "Error", "Failed to record payment.")
