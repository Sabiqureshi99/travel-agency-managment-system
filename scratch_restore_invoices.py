import os
import re

accounts_file = "ui/pages/accounting/accounts_page.py"
with open(accounts_file, "r", encoding="utf-8") as f:
    accounts = f.read()

# 1. Rename the quotation UI elements to use 'quot_' prefix instead of 'inv_' prefix
def rename_prefix(code, old, new):
    return code.replace(old, new)

# We only want to rename them where they apply to quotations. Since they currently replaced invoices, they are all named inv_.
# Actually, it's easier to just rename everything related to quotations to quot_, then re-insert invoices.
for var in ['inv_search', 'inv_status_filter', 'tbl_inv', 'btn_inv_prev', 'lbl_inv_page', 'btn_inv_next', 'inv_page', 'total_inv']:
    accounts = rename_prefix(accounts, var, var.replace('inv_', 'quot_').replace('inv', 'quot'))

# Now let's inject the Invoices Tab UI setup back in.
invoices_tab_ui = """
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
        
"""

accounts = accounts.replace('# --- Quotations Tab ---', invoices_tab_ui + '        # --- Quotations Tab ---')
accounts = accounts.replace('# --- Invoices Tab ---', invoices_tab_ui + '        # --- Quotations Tab ---', 1) # Handle case where it's still named Invoices Tab comment

# Add pagination logic for invoices
pagination_logic = """
    def _inv_prev_page(self):
        if self.inv_page > 1:
            self.inv_page -= 1
            self.refresh()
            
    def _inv_next_page(self):
        import math
        if self.inv_page < max(1, math.ceil(self.total_inv / self.page_size)):
            self.inv_page += 1
            self.refresh()
"""
accounts = accounts.replace('def _quot_prev_page(self):', pagination_logic + '\n    def _quot_prev_page(self):')

# Add _on_inv_search
search_logic = """
    def _on_inv_search(self):
        query = self.inv_search.text().strip()
        status = self.inv_status_filter.currentText()
        if status == "All Statuses":
            status = ""
        combined = f"{query} {status}".strip()
        self.inv_page = 1
        self.viewmodel.load_invoices(query=combined, skip=0, limit=self.page_size)
"""
accounts = accounts.replace('def _on_quot_search(self):', search_logic + '\n    def _on_quot_search(self):')

# Add connection
accounts = accounts.replace('self.viewmodel.quotations_loaded.connect(self._on_quotations_loaded)', 'self.viewmodel.invoices_loaded.connect(self._on_invoices_loaded)\n        self.viewmodel.quotations_loaded.connect(self._on_quotations_loaded)')

# Add init vars
accounts = accounts.replace('self.quot_page = 1', 'self.inv_page = 1\n        self.quot_page = 1')
accounts = accounts.replace('self.total_quot = 0', 'self.total_inv = 0\n        self.total_quot = 0')

# Update refresh
refresh_logic = """
        inv_query = self.inv_search.text().strip()
        inv_status = self.inv_status_filter.currentText()
        if inv_status == "All Statuses":
            inv_status = ""
        inv_combined = f"{inv_query} {inv_status}".strip()
        self.viewmodel.load_invoices(query=inv_combined, skip=(self.inv_page - 1) * self.page_size, limit=self.page_size)
"""
accounts = accounts.replace('self.viewmodel.load_quotations', refresh_logic + '\n        self.viewmodel.load_quotations')

# Re-add _on_invoices_loaded
on_invoices_loaded = """
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
"""

accounts = accounts.replace('def _on_quotations_loaded', on_invoices_loaded + '\n    def _on_quotations_loaded')

with open(accounts_file, "w", encoding="utf-8") as f:
    f.write(accounts)

print("Done restoring invoices alongside quotations.")
