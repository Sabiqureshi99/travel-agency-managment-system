from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QTabWidget, QTableWidget, 
                               QHeaderView, QTableWidgetItem, QAbstractItemView,
                               QLineEdit, QComboBox)
from PySide6.QtCore import Qt
from viewmodels.accounting_viewmodel import AccountingViewModel
from utils.formatters import format_currency, format_date

class AccountingPage(QWidget):
    def __init__(self, current_user, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.viewmodel = AccountingViewModel()
        
        self.inv_page = 1
        self.quot_page = 1
        self.rec_page = 1
        self.cash_page = 1
        self.cust_page = 1
        self.page_size = 50
        
        self.total_inv = 0
        self.total_quot = 0
        self.total_rec = 0
        self.total_cash = 0
        self.total_cust = 0
        
        self._setup_ui()
        self._connect_signals()
        self.refresh()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        header = QHBoxLayout()
        title = QLabel("Accounting & Finance")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #FFFFFF;")
        
        self.btn_invoice = QPushButton("💳 New Invoice")
        self.btn_invoice.setObjectName("btn_primary")
        self.btn_invoice.setShortcut("Return")
        
        self.btn_quotation = QPushButton("📝 Create Quotation")
        self.btn_quotation.setObjectName("btn_primary")
        self.btn_quotation.setStyleSheet("background-color: #8b5cf6;")
        
        self.btn_receipt = QPushButton("💰 Receive Payment")
        self.btn_receipt.setObjectName("btn_success")
        
        self.btn_expense = QPushButton("📉 Log Expense")
        self.btn_expense.setObjectName("btn_danger")
        
        self.btn_vendor_payment = QPushButton("🏦 Vendor Payment")
        self.btn_vendor_payment.setObjectName("btn_warning")
        
        self.btn_withdrawal = QPushButton("🏧 Withdrawal")
        self.btn_withdrawal.setObjectName("btn_secondary")
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.btn_invoice)
        header.addWidget(self.btn_quotation)
        header.addWidget(self.btn_receipt)
        header.addWidget(self.btn_expense)
        header.addWidget(self.btn_vendor_payment)
        header.addWidget(self.btn_withdrawal)
        layout.addLayout(header)
        
        self.tabs = QTabWidget()
        
        
        # --- Invoices Tab ---
        tab_inv = QWidget()
        l_inv = QVBoxLayout(tab_inv)
        
        inv_search_row = QHBoxLayout()
        self.inv_search = QLineEdit()
        self.inv_search.setPlaceholderText("Search Invoice #, Customer, Status...")
        self.inv_search.setFixedWidth(320)
        self.inv_search.textChanged.connect(self._on_inv_search)
        self.inv_status_filter = QComboBox()
        self.inv_status_filter.addItems(["All Statuses", "Paid", "Unpaid", "Partial"])
        self.inv_status_filter.currentTextChanged.connect(self._on_inv_search)
        inv_search_row.addWidget(self.inv_search)
        inv_search_row.addWidget(self.inv_status_filter)
        inv_search_row.addStretch()
        l_inv.addLayout(inv_search_row)
        
        self.tbl_inv = self._create_table(["Invoice #", "Date", "Customer", "Subtotal", "Tax", "Total", "Paid", "Balance", "Status", "Actions"])
        l_inv.addWidget(self.tbl_inv)
        
        inv_pagination = QHBoxLayout()
        inv_pagination.addStretch()
        self.btn_inv_prev = QPushButton("< Prev")
        self.lbl_inv_page = QLabel("Page 1 of 1")
        self.btn_inv_next = QPushButton("Next >")
        self.btn_inv_prev.clicked.connect(self._inv_prev_page)
        self.btn_inv_next.clicked.connect(self._inv_next_page)
        inv_pagination.addWidget(self.btn_inv_prev)
        inv_pagination.addWidget(self.lbl_inv_page)
        inv_pagination.addWidget(self.btn_inv_next)
        inv_pagination.addStretch()
        l_inv.addLayout(inv_pagination)
        
        self.tabs.addTab(tab_inv, "Invoices")
        
        # --- Quotations Tab ---
        tab_quot = QWidget()
        l_quot = QVBoxLayout(tab_quot)
        
        # Invoice search bar
        quot_search_row = QHBoxLayout()
        self.quot_search = QLineEdit()
        self.quot_search.setPlaceholderText("Search Invoice #, Customer, Status...")
        self.quot_search.setFixedWidth(320)
        self.quot_search.textChanged.connect(self._on_quot_search)
        self.quot_status_filter = QComboBox()
        self.quot_status_filter.addItems(["All Statuses", "Paid", "Unpaid", "Partial"])
        self.quot_status_filter.currentTextChanged.connect(self._on_quot_search)
        quot_search_row.addWidget(self.quot_search)
        quot_search_row.addWidget(self.quot_status_filter)
        quot_search_row.addStretch()
        l_quot.addLayout(quot_search_row)
        
        self.tbl_quot = self._create_table(["Quote #", "Date", "Guest Name", "Phone", "Total Amount", "Status", "Actions"])
        l_quot.addWidget(self.tbl_quot)
        
        quot_pagination = QHBoxLayout()
        quot_pagination.addStretch()
        self.btn_quot_prev = QPushButton("< Prev")
        self.lbl_quot_page = QLabel("Page 1 of 1")
        self.btn_quot_next = QPushButton("Next >")
        self.btn_quot_prev.clicked.connect(self._inv_prev_page)
        self.btn_quot_next.clicked.connect(self._inv_next_page)
        quot_pagination.addWidget(self.btn_quot_prev)
        quot_pagination.addWidget(self.lbl_quot_page)
        quot_pagination.addWidget(self.btn_quot_next)
        quot_pagination.addStretch()
        l_quot.addLayout(quot_pagination)
        
        self.tabs.addTab(tab_quot, "Quotations")
        
        # --- Receipts Tab ---
        tab_rec = QWidget()
        l_rec = QVBoxLayout(tab_rec)
        
        # Receipt search bar
        rec_search_row = QHBoxLayout()
        self.rec_search = QLineEdit()
        self.rec_search.setPlaceholderText("Search Receipt #, Customer, Invoice Ref...")
        self.rec_search.setFixedWidth(320)
        self.rec_search.textChanged.connect(self._on_rec_search)
        rec_search_row.addWidget(self.rec_search)
        rec_search_row.addStretch()
        l_rec.addLayout(rec_search_row)
        
        self.tbl_rec = self._create_table(["Receipt #", "Date", "Customer", "Invoice Ref", "Amount", "Method"])
        l_rec.addWidget(self.tbl_rec)
        
        rec_pagination = QHBoxLayout()
        rec_pagination.addStretch()
        self.btn_rec_prev = QPushButton("< Prev")
        self.lbl_rec_page = QLabel("Page 1 of 1")
        self.btn_rec_next = QPushButton("Next >")
        self.btn_rec_prev.clicked.connect(self._rec_prev_page)
        self.btn_rec_next.clicked.connect(self._rec_next_page)
        rec_pagination.addWidget(self.btn_rec_prev)
        rec_pagination.addWidget(self.lbl_rec_page)
        rec_pagination.addWidget(self.btn_rec_next)
        rec_pagination.addStretch()
        l_rec.addLayout(rec_pagination)
        
        self.tabs.addTab(tab_rec, "Receipts")
        
        # --- Cash Book Tab ---
        tab_cash = QWidget()
        l_cash = QVBoxLayout(tab_cash)
        
        # Top bar with current balance
        cash_header_row = QHBoxLayout()
        
        self.cash_search = QLineEdit()
        self.cash_search.setPlaceholderText("Search Ref, Description, Method...")
        self.cash_search.setFixedWidth(320)
        self.cash_search.textChanged.connect(self._on_cash_search)
        
        self.lbl_cash_balance = QLabel("Current Balance: Rs. 0.00")
        self.lbl_cash_balance.setStyleSheet("font-size: 18px; font-weight: bold; color: #10B981;")
        
        cash_header_row.addWidget(self.cash_search)
        cash_header_row.addStretch()
        cash_header_row.addWidget(self.lbl_cash_balance)
        l_cash.addLayout(cash_header_row)
        
        self.tbl_cash = self._create_table(["Date", "Type", "Ref/ID", "Description", "Method", "Cash IN", "Cash OUT", "Balance"])
        l_cash.addWidget(self.tbl_cash)
        
        cash_pagination = QHBoxLayout()
        cash_pagination.addStretch()
        self.btn_cash_prev = QPushButton("< Prev")
        self.lbl_cash_page = QLabel("Page 1 of 1")
        self.btn_cash_next = QPushButton("Next >")
        self.btn_cash_prev.clicked.connect(self._cash_prev_page)
        self.btn_cash_next.clicked.connect(self._cash_next_page)
        cash_pagination.addWidget(self.btn_cash_prev)
        cash_pagination.addWidget(self.lbl_cash_page)
        cash_pagination.addWidget(self.btn_cash_next)
        cash_pagination.addStretch()
        l_cash.addLayout(cash_pagination)
        
        self.tabs.addTab(tab_cash, "Cash Book")
        
        # --- Customer Ledgers Tab ---
        tab_cust_ledg = QWidget()
        l_cust_ledg = QVBoxLayout(tab_cust_ledg)
        
        cust_search_row = QHBoxLayout()
        self.cust_search = QLineEdit()
        self.cust_search.setPlaceholderText("Search Customer by Name or Phone...")
        self.cust_search.setFixedWidth(320)
        self.cust_search.textChanged.connect(self._on_cust_search)
        cust_search_row.addWidget(self.cust_search)
        
        self.btn_global_cust_report = QPushButton("📄 Global Customer Ledger")
        self.btn_global_cust_report.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_global_cust_report.setStyleSheet("padding: 8px; background-color: #8b5cf6; color: white; border-radius: 4px; font-weight: bold;")
        self.btn_global_cust_report.clicked.connect(self._generate_global_customer_summary)
        cust_search_row.addWidget(self.btn_global_cust_report)
        
        cust_search_row.addStretch()
        l_cust_ledg.addLayout(cust_search_row)
        
        self.tbl_cust = self._create_table(["Customer Code", "Customer Name", "Phone", "Total Billed", "Total Paid", "Balance", "Actions"])
        self.tbl_cust.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.tbl_cust.setColumnWidth(6, 120)
        self.tbl_cust.verticalHeader().setDefaultSectionSize(40)
        self.tbl_cust.cellDoubleClicked.connect(self._on_cust_double_clicked)
        l_cust_ledg.addWidget(self.tbl_cust)
        
        cust_pagination = QHBoxLayout()
        cust_pagination.addStretch()
        self.btn_cust_prev = QPushButton("< Prev")
        self.lbl_cust_page = QLabel("Page 1 of 1")
        self.btn_cust_next = QPushButton("Next >")
        self.btn_cust_prev.clicked.connect(self._cust_prev_page)
        self.btn_cust_next.clicked.connect(self._cust_next_page)
        cust_pagination.addWidget(self.btn_cust_prev)
        cust_pagination.addWidget(self.lbl_cust_page)
        cust_pagination.addWidget(self.btn_cust_next)
        cust_pagination.addStretch()
        l_cust_ledg.addLayout(cust_pagination)
        
        self.tabs.addTab(tab_cust_ledg, "Customer Ledgers")
        
        layout.addWidget(self.tabs)
        
    def _create_table(self, headers: list[str]) -> QTableWidget:
        tbl = QTableWidget(0, len(headers))
        tbl.setHorizontalHeaderLabels(headers)
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tbl.verticalHeader().setVisible(False)
        tbl.setShowGrid(False)
        tbl.setStyleSheet("""
            QTableWidget {
                background-color: #252836;
                border: 1px solid #2A2D3E;
                border-radius: 8px;
                padding: 5px;
                color: #E2E8F0;
            }
            QHeaderView::section {
                background-color: transparent;
                color: #8892B0;
                font-weight: bold;
                border: none;
                border-bottom: 1px solid #2A2D3E;
                padding-bottom: 8px;
            }
            QTableWidget::item {
                border-bottom: 1px solid #2A2D3E;
                padding: 10px 5px;
            }
        """)
        return tbl
        
    def _connect_signals(self):
        self.viewmodel.invoices_loaded.connect(self._on_invoices_loaded)
        self.viewmodel.quotations_loaded.connect(self._on_quotations_loaded)
        self.viewmodel.receipts_loaded.connect(self._on_receipts_loaded)
        self.viewmodel.cashbook_loaded.connect(self._on_cashbook_loaded)
        self.viewmodel.customer_balances_loaded.connect(self._on_customer_balances_loaded)
        self.viewmodel.error_occurred.connect(self._on_error)
        
        # Connect global signals for background refresh
        from core.signals import app_signals
        app_signals.umrah_checkout_completed.connect(self.refresh)
        app_signals.invoice_generated.connect(self.refresh)
        app_signals.payment_processed.connect(self.refresh)
        app_signals.payment_received.connect(self.refresh)
        app_signals.flight_added.connect(self.refresh)
        app_signals.hotel_added.connect(self.refresh)
        app_signals.visa_added.connect(self.refresh)
        app_signals.transport_added.connect(self.refresh)
        
        self.btn_invoice.clicked.connect(self._open_invoice_form)
        self.btn_quotation.clicked.connect(self._open_quotation_builder)
        self.btn_receipt.clicked.connect(self._open_receipt_form)
        self.btn_expense.clicked.connect(self._open_expense_dialog)
        self.btn_vendor_payment.clicked.connect(self._open_vendor_payment_dialog)
        self.btn_withdrawal.clicked.connect(self._open_withdrawal_dialog)
        
    def _inv_prev_page(self):
        if self.quot_page > 1:
            self.quot_page -= 1
            self.refresh()
            
    def _inv_next_page(self):
        import math
        if self.quot_page < max(1, math.ceil(self.total_quot / self.page_size)):
            self.quot_page += 1
            self.refresh()
            
    def _rec_prev_page(self):
        if self.rec_page > 1:
            self.rec_page -= 1
            self.refresh()
            
    def _rec_next_page(self):
        import math
        if self.rec_page < max(1, math.ceil(self.total_rec / self.page_size)):
            self.rec_page += 1
            self.refresh()
            
    def _cash_prev_page(self):
        if self.cash_page > 1:
            self.cash_page -= 1
            self.refresh()
            
    def _cash_next_page(self):
        import math
        if self.cash_page < max(1, math.ceil(self.total_cash / self.page_size)):
            self.cash_page += 1
            self.refresh()
            
    def _cust_prev_page(self):
        if self.cust_page > 1:
            self.cust_page -= 1
            self.refresh()
            
    def _cust_next_page(self):
        import math
        if self.cust_page < max(1, math.ceil(self.total_cust / self.page_size)):
            self.cust_page += 1
            self.refresh()
        
    
    def _on_invoices_loaded(self, invoices, total_count):
        self.total_inv = total_count
        import math
        from PySide6.QtWidgets import QTableWidgetItem, QPushButton
        from PySide6.QtCore import Qt
        from utils.formatters import format_date, format_currency
        
        total_pages = max(1, math.ceil(self.total_inv / self.page_size))
        self.lbl_inv_page.setText(f"Page {self.inv_page} of {total_pages}")
        self.btn_inv_prev.setEnabled(self.inv_page > 1)
        self.btn_inv_next.setEnabled(self.inv_page < total_pages)
        
        self.tbl_inv.setRowCount(0)
        for row, inv in enumerate(invoices):
            self.tbl_inv.insertRow(row)
            customer_name = inv.customer.full_name if inv.customer else "Unknown"
            self.tbl_inv.setItem(row, 0, QTableWidgetItem(inv.invoice_number))
            
            self.tbl_inv.setItem(row, 1, QTableWidgetItem(format_date(inv.issue_date)))
            self.tbl_inv.setItem(row, 2, QTableWidgetItem(customer_name))
            self.tbl_inv.setItem(row, 3, QTableWidgetItem(format_currency(inv.subtotal)))
            self.tbl_inv.setItem(row, 4, QTableWidgetItem(format_currency(inv.tax_amount)))
            self.tbl_inv.setItem(row, 5, QTableWidgetItem(format_currency(inv.total_amount)))
            self.tbl_inv.setItem(row, 6, QTableWidgetItem(format_currency(inv.amount_paid)))
            self.tbl_inv.setItem(row, 7, QTableWidgetItem(format_currency(inv.amount_remaining)))
            
            status_item = QTableWidgetItem(inv.status)
            if inv.status == 'Paid':
                status_item.setForeground(Qt.GlobalColor.green)
            elif inv.status == 'Unpaid':
                status_item.setForeground(Qt.GlobalColor.red)
            elif inv.status == 'Partial':
                status_item.setForeground(Qt.GlobalColor.yellow)
            self.tbl_inv.setItem(row, 8, status_item)
            
            btn_print = QPushButton("Print")
            btn_print.setStyleSheet("background-color: #3B82F6; color: white; border-radius: 4px; padding: 4px 8px;")
            btn_print.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_print.clicked.connect(lambda checked=False, i=inv: self._print_invoice(i))
            self.tbl_inv.setCellWidget(row, 9, btn_print)

    def _print_invoice(self, invoice):
        import os
        from services.invoice_generator import InvoiceGenerator
        filepath = os.path.abspath(f"Invoice_{invoice.invoice_number}.pdf")
        try:
            InvoiceGenerator.generate_invoice_pdf(invoice, filepath)
            os.startfile(filepath)
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Failed to generate PDF: {str(e)}")

    def _on_quotations_loaded(self, quotations, total_count):
        self.total_quot = total_count
        import math
        total_pages = max(1, math.ceil(self.total_quot / self.page_size))
        self.lbl_quot_page.setText(f"Page {self.quot_page} of {total_pages}")
        self.btn_quot_prev.setEnabled(self.quot_page > 1)
        self.btn_quot_next.setEnabled(self.quot_page < total_pages)
        
        self.tbl_quot.setRowCount(0)
        for row, q in enumerate(quotations):
            self.tbl_quot.insertRow(row)
            
            self.tbl_quot.setItem(row, 0, QTableWidgetItem(q.id[:8].upper()))
            self.tbl_quot.setItem(row, 1, QTableWidgetItem(format_date(q.date_created)))
            self.tbl_quot.setItem(row, 2, QTableWidgetItem(q.guest_name or 'Walk-in'))
            self.tbl_quot.setItem(row, 3, QTableWidgetItem(q.guest_phone or '-'))
            self.tbl_quot.setItem(row, 4, QTableWidgetItem(format_currency(q.total_amount)))
            
            status_item = QTableWidgetItem(q.status)
            if q.status == 'Accepted':
                status_item.setForeground(Qt.GlobalColor.green)
            elif q.status == 'Expired':
                status_item.setForeground(Qt.GlobalColor.red)
            else:
                status_item.setForeground(Qt.GlobalColor.yellow)
            self.tbl_quot.setItem(row, 5, status_item)
            
            btn_print = QPushButton("Print Quote")
            btn_print.setStyleSheet("background-color: #3B82F6; color: white; border-radius: 4px; padding: 4px 8px;")
            btn_print.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_print.clicked.connect(lambda checked=False, q_id=q.id, g_name=q.guest_name: self._print_quotation(q_id, g_name))
            self.tbl_quot.setCellWidget(row, 6, btn_print)
            
    def _print_quotation(self, quotation_id, guest_name):
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        from services.pdf_engine import QuotationPDFEngine
        import os
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Quotation PDF",
            f"Quotation_{guest_name or 'Walk-in'}.pdf",
            "PDF Files (*.pdf)"
        )
        
        if filepath:
            try:
                QuotationPDFEngine.generate_quotation_pdf(filepath, quotation_id)
                QMessageBox.information(self, "Success", "Quotation PDF generated successfully!")
                QDesktopServices.openUrl(QUrl.fromLocalFile(filepath))
            except Exception as e:
                import logging
                logging.exception("Failed to generate PDF")
                QMessageBox.critical(self, "Error", f"Failed to generate PDF: {str(e)}")
            
    def _on_receipts_loaded(self, receipts, total_count):
        self.total_rec = total_count
        import math
        total_pages = max(1, math.ceil(self.total_rec / self.page_size))
        self.lbl_rec_page.setText(f"Page {self.rec_page} of {total_pages}")
        self.btn_rec_prev.setEnabled(self.rec_page > 1)
        self.btn_rec_next.setEnabled(self.rec_page < total_pages)
        
        self.tbl_rec.setRowCount(0)
        for row, rec in enumerate(receipts):
            self.tbl_rec.insertRow(row)
            
            customer_name = rec.customer.full_name if rec.customer else "Unknown"
            inv_number = rec.invoice.invoice_number if rec.invoice else "Advance"
            
            self.tbl_rec.setItem(row, 0, QTableWidgetItem(rec.receipt_number))
            self.tbl_rec.setItem(row, 1, QTableWidgetItem(format_date(rec.receipt_date)))
            self.tbl_rec.setItem(row, 2, QTableWidgetItem(customer_name))
            self.tbl_rec.setItem(row, 3, QTableWidgetItem(inv_number))
            self.tbl_rec.setItem(row, 4, QTableWidgetItem(format_currency(rec.amount)))
            self.tbl_rec.setItem(row, 5, QTableWidgetItem(rec.payment_method))
            
    def _on_error(self, message):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.warning(self, "Accounting Error", message)
        
    def _open_invoice_form(self):
        from ui.pages.accounting.invoice_form import InvoiceForm
        form = InvoiceForm(self.viewmodel, self.current_user.id, self)
        if form.exec():
            self.refresh()

    def _open_quotation_builder(self):
        from ui.dialogs.quotation_builder_dialog import QuotationBuilderDialog
        dialog = QuotationBuilderDialog(self)
        if dialog.exec():
            self.refresh()
            
    def _open_receipt_form(self):
        from ui.pages.accounting.receipt_form import ReceiptForm
        form = ReceiptForm(self.viewmodel, self.current_user.id, self)
        if form.exec():
            self.refresh()
            
    def _open_expense_dialog(self):
        from ui.pages.accounting.financial_dialogs import ExpenseDialog
        dialog = ExpenseDialog(self)
        dialog.exec()
        
    def _open_vendor_payment_dialog(self):
        from ui.pages.accounting.financial_dialogs import VendorPaymentDialog
        dialog = VendorPaymentDialog(self)
        dialog.exec()
        
    def _open_withdrawal_dialog(self):
        from ui.pages.accounting.financial_dialogs import WithdrawalDialog
        dialog = WithdrawalDialog(self)
        dialog.exec()
            
    
    def _on_inv_search(self):
        query = self.inv_search.text().strip()
        status = self.inv_status_filter.currentText()
        if status == "All Statuses":
            status = ""
        combined = f"{query} {status}".strip()
        self.inv_page = 1
        self.viewmodel.load_invoices(query=combined, skip=0, limit=self.page_size)

    def _on_quot_search(self):
        query = self.quot_search.text().strip()
        status = self.quot_status_filter.currentText()
        if status == "All Statuses":
            status = ""
        combined = f"{query} {status}".strip()
        self.quot_page = 1
        self.viewmodel.load_quotations(query=combined, skip=0, limit=self.page_size)

    def _on_rec_search(self):
        query = self.rec_search.text().strip()
        self.rec_page = 1
        self.viewmodel.load_receipts(query=query, skip=0, limit=self.page_size)

    def _on_cash_search(self):
        query = self.cash_search.text().strip()
        self.cash_page = 1
        self.viewmodel.load_cashbook(query=query, skip=0, limit=self.page_size)
        
    def _on_cashbook_loaded(self, ledger, total_count, total_balance):
        self.total_cash = total_count
        import math
        total_pages = max(1, math.ceil(self.total_cash / self.page_size))
        self.lbl_cash_page.setText(f"Page {self.cash_page} of {total_pages}")
        self.btn_cash_prev.setEnabled(self.cash_page > 1)
        self.btn_cash_next.setEnabled(self.cash_page < total_pages)
        
        self.tbl_cash.setRowCount(0)
        
        # If there's no active search, update the large KPI label
        if not self.cash_search.text().strip():
            self.lbl_cash_balance.setText(f"Current Balance: Rs. {total_balance:,.2f}")
            if total_balance >= 0:
                self.lbl_cash_balance.setStyleSheet("font-size: 18px; font-weight: bold; color: #10B981;")
            else:
                self.lbl_cash_balance.setStyleSheet("font-size: 18px; font-weight: bold; color: #EF4444;")
                
        for row, tx in enumerate(ledger):
            self.tbl_cash.insertRow(row)
            self.tbl_cash.setItem(row, 0, QTableWidgetItem(format_date(tx["date"])))
            self.tbl_cash.setItem(row, 1, QTableWidgetItem(tx["type"]))
            self.tbl_cash.setItem(row, 2, QTableWidgetItem(tx["reference"]))
            self.tbl_cash.setItem(row, 3, QTableWidgetItem(tx["description"]))
            self.tbl_cash.setItem(row, 4, QTableWidgetItem(tx["method"]))
            
            # Cash IN
            item_in = QTableWidgetItem(format_currency(tx["cash_in"]) if tx["cash_in"] > 0 else "-")
            if tx["cash_in"] > 0:
                item_in.setForeground(Qt.GlobalColor.green)
            self.tbl_cash.setItem(row, 5, item_in)
            
            # Cash OUT
            item_out = QTableWidgetItem(format_currency(tx["cash_out"]) if tx["cash_out"] > 0 else "-")
            if tx["cash_out"] > 0:
                item_out.setForeground(Qt.GlobalColor.red)
            self.tbl_cash.setItem(row, 6, item_out)
            
            # Balance
            bal_item = QTableWidgetItem(format_currency(tx["balance"]))
            if tx["balance"] < 0:
                bal_item.setForeground(Qt.GlobalColor.red)
            self.tbl_cash.setItem(row, 7, bal_item)
            
    def refresh(self):
        quot_query = self.quot_search.text().strip() if hasattr(self, 'quot_search') else ""
        quot_status = self.quot_status_filter.currentText() if hasattr(self, 'quot_status_filter') else ""
        if quot_status == "All Statuses":
            quot_status = ""
        quot_combined = f"{quot_query} {quot_status}".strip()
        
        inv_query = self.inv_search.text().strip() if hasattr(self, 'inv_search') else ""
        inv_status = self.inv_status_filter.currentText() if hasattr(self, 'inv_status_filter') else ""
        if inv_status == "All Statuses":
            inv_status = ""
        inv_combined = f"{inv_query} {inv_status}".strip()
        
        rec_query = self.rec_search.text().strip() if hasattr(self, 'rec_search') else ""
        cash_query = self.cash_search.text().strip() if hasattr(self, 'cash_search') else ""
        cust_query = self.cust_search.text().strip() if hasattr(self, 'cust_search') else ""
        
        self.viewmodel.load_invoices(query=inv_combined, skip=(self.inv_page - 1) * self.page_size, limit=self.page_size)
        self.viewmodel.load_quotations(query=quot_combined, skip=(self.quot_page - 1) * self.page_size, limit=self.page_size)
        self.viewmodel.load_receipts(query=rec_query, skip=(self.rec_page - 1) * self.page_size, limit=self.page_size)
        self.viewmodel.load_cashbook(query=cash_query, skip=(self.cash_page - 1) * self.page_size, limit=self.page_size)
        self.viewmodel.load_customer_balances(query=cust_query, skip=(self.cust_page - 1) * self.page_size, limit=self.page_size)

    def _on_cust_search(self):
        query = self.cust_search.text().strip()
        self.cust_page = 1
        self.viewmodel.load_customer_balances(query=query, skip=0, limit=self.page_size)
        
    def _on_customer_balances_loaded(self, balances, total_count):
        self.total_cust = total_count
        import math
        total_pages = max(1, math.ceil(self.total_cust / self.page_size))
        self.lbl_cust_page.setText(f"Page {self.cust_page} of {total_pages}")
        self.btn_cust_prev.setEnabled(self.cust_page > 1)
        self.btn_cust_next.setEnabled(self.cust_page < total_pages)
        
        self.tbl_cust.setRowCount(0)
        for row, data in enumerate(balances):
            self.tbl_cust.insertRow(row)
            
            customer = data['customer']
            
            self.tbl_cust.setItem(row, 0, QTableWidgetItem(customer.customer_code))
            self.tbl_cust.setItem(row, 1, QTableWidgetItem(customer.full_name))
            self.tbl_cust.setItem(row, 2, QTableWidgetItem(customer.phone_primary))
            
            self.tbl_cust.setItem(row, 3, QTableWidgetItem(format_currency(data['total_billed'])))
            self.tbl_cust.setItem(row, 4, QTableWidgetItem(format_currency(data['total_paid'])))
            
            bal_item = QTableWidgetItem(format_currency(data['balance']))
            if data['balance'] > 0:
                bal_item.setForeground(Qt.GlobalColor.red)
            else:
                bal_item.setForeground(Qt.GlobalColor.green)
            self.tbl_cust.setItem(row, 5, bal_item)
            
            btn_view = QPushButton("View Ledger")
            btn_view.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_view.setStyleSheet("padding: 4px; background-color: #3b82f6; color: white; border-radius: 4px; font-weight: bold;")
            btn_view.clicked.connect(lambda checked=False, cid=customer.id: self._open_customer_ledger(cid))
            
            btn_report = QPushButton("📄 Global Report")
            btn_report.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_report.setStyleSheet("padding: 4px; background-color: #8b5cf6; color: white; border-radius: 4px; font-weight: bold;")
            btn_report.clicked.connect(lambda checked=False, cid=customer.id: self._generate_customer_report(cid))
            
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(15, 6, 15, 6)
            action_layout.addWidget(btn_view)
            action_layout.addWidget(btn_report)
            
            self.tbl_cust.setCellWidget(row, 6, action_widget)
            self.tbl_cust.setRowHeight(row, 50)
            
            # Store customer id in row data for double click
            self.tbl_cust.item(row, 0).setData(Qt.ItemDataRole.UserRole, customer.id)
            
    def _on_cust_double_clicked(self, row, column):
        item = self.tbl_cust.item(row, 0)
        if item:
            customer_id = item.data(Qt.ItemDataRole.UserRole)
            if customer_id:
                self._open_customer_ledger(customer_id)
            
    def _open_customer_ledger(self, customer_id: str):
        from ui.pages.accounting.customer_ledger_dialog import CustomerLedgerDialog
        dialog = CustomerLedgerDialog(customer_id, self.viewmodel, self)
        dialog.exec()
        self.refresh()

    def _generate_customer_report(self, customer_id: str):
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        from services.pdf_engine import GlobalPDFEngine
        from services.customer_service import CustomerService
        
        customer = CustomerService().get_customer_by_id(customer_id)
        if not customer:
            QMessageBox.warning(self, "Error", "Customer not found.")
            return
            
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Customer Report",
            f"Customer_Report_{customer.full_name}.pdf",
            "PDF Files (*.pdf)"
        )
        if not filepath:
            return
            
        try:
            # We fetch all ledgers for this customer
            raw_ledger = self.viewmodel._service.get_customer_ledger(customer_id)
            
            transactions = []
            for tx in raw_ledger:
                # the service returns: date, type, reference, debit, credit, balance
                transactions.append({
                    'date': tx['date'].strftime("%Y-%m-%d") if hasattr(tx['date'], 'strftime') else tx['date'],
                    'ref': tx['reference'] or 'N/A',
                    'source': tx['type'] or 'N/A',
                    'billed': tx['debit'],
                    'paid': tx['credit']
                })
                    
            engine = GlobalPDFEngine()
            engine.generate_customer_report(filepath, customer.full_name, transactions, "All Time")
            
            QMessageBox.information(self, "Success", f"Customer Report generated successfully:\n{filepath}")
            QDesktopServices.openUrl(QUrl.fromLocalFile(filepath))
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate report: {e}")

    def _generate_global_customer_summary(self):
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        from services.pdf_engine import GlobalPDFEngine
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Global Customer Ledger",
            "Global_Customer_Ledger.pdf",
            "PDF Files (*.pdf)"
        )
        if not filepath:
            return
            
        try:
            # We want to dump all current customers loaded or a fresh query
            # Since self.viewmodel.load_customer_balances supports pagination, 
            # we should fetch ALL customers for the global report.
            all_balances_result = self.viewmodel._service.get_customer_balances(query="", skip=0, limit=1000000)
            all_balances = all_balances_result['items']
            
            formatted_balances = []
            for b in all_balances:
                customer = b['customer']
                formatted_balances.append({
                    'code': customer.customer_code,
                    'name': customer.full_name,
                    'phone': customer.phone_primary,
                    'billed': b['total_billed'],
                    'paid': b['total_paid'],
                    'balance': b['balance']
                })
                
            engine = GlobalPDFEngine()
            engine.generate_global_customer_summary(filepath, formatted_balances, "All Time")
            
            QMessageBox.information(self, "Success", f"Global Customer Ledger generated successfully:\n{filepath}")
            QDesktopServices.openUrl(QUrl.fromLocalFile(filepath))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate global report: {e}")

    def _print_quotation(self, quotation_id, guest_name):
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        from services.pdf_engine import QuotationPDFEngine
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Quotation PDF",
            f"Quotation_{guest_name or 'Walk-in'}.pdf",
            "PDF Files (*.pdf)"
        )
        
        if filepath:
            try:
                QuotationPDFEngine.generate_quotation_pdf(filepath, quotation_id)
                QMessageBox.information(self, "Success", "Quotation PDF generated successfully!")
                QDesktopServices.openUrl(QUrl.fromLocalFile(filepath))
            except Exception as e:
                import logging
                logging.exception("Failed to generate PDF")
                QMessageBox.critical(self, "Error", f"Failed to generate PDF: {str(e)}")
