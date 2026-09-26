import datetime
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QTableWidget, QTableWidgetItem, QPushButton, 
                               QHeaderView, QMessageBox, QWidget, QAbstractItemView)
from PySide6.QtCore import Qt, QDate
from config.database import get_session
from models.vendor import Vendor, VendorLedger
from ui.pages.vendors.vendor_form import VendorForm
from ui.pages.vendors.vendor_ledger_popups import (
    VendorAddBillDialog, VendorMakePaymentDialog, 
    VendorExportDialog, VendorEditTransactionDialog
)

class VendorLedgerDialog(QDialog):
    def __init__(self, vendor_id: str, parent=None):
        super().__init__(parent)
        self.vendor_id = vendor_id
        self.setWindowTitle("Vendor Ledger")
        self.setMinimumSize(1150, 700)
        self.resize(1150, 700)
        self._setup_ui()
        self.load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Header
        self.lbl_title = QLabel("Ledger: Loading...")
        self.lbl_title.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.lbl_balance = QLabel("Balance: PKR 0.00")
        self.lbl_balance.setStyleSheet("font-size: 16px; font-weight: bold; color: #4CAF50;")
        
        header_layout = QHBoxLayout()
        header_layout.addWidget(self.lbl_title)
        header_layout.addStretch()
        header_layout.addWidget(self.lbl_balance)
        layout.addLayout(header_layout)

        # Toolbar
        toolbar = QHBoxLayout()
        btn_edit_profile = QPushButton("Edit Profile")
        btn_edit_profile.clicked.connect(self.edit_profile)
        btn_add_bill = QPushButton("Add Bill")
        btn_add_bill.clicked.connect(self.add_bill)
        btn_make_payment = QPushButton("Make Payment")
        btn_make_payment.clicked.connect(self.make_payment)
        btn_export = QPushButton("Export PDF")
        btn_export.clicked.connect(self.export_pdf)
        
        toolbar.addWidget(btn_edit_profile)
        toolbar.addWidget(btn_add_bill)
        toolbar.addWidget(btn_make_payment)
        toolbar.addWidget(btn_export)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Table
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "Date", "Description", "Ref Booking", "Debit (Paid)", "Credit (Billed)", "Balance", "Actions"
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(6, 100)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

    def load_data(self):
        self.table.setRowCount(0)
        try:
            with get_session() as session:
                vendor = session.get(Vendor, self.vendor_id)
                if not vendor:
                    QMessageBox.warning(self, "Error", "Vendor not found.")
                    self.reject()
                    return
                
                self.lbl_title.setText(f"Ledger: {vendor.company_name} ({vendor.vendor_type})")
                
                # Opening balance row
                running_balance = float(vendor.opening_balance or 0)
                self.table.insertRow(0)
                self.table.setItem(0, 0, QTableWidgetItem("-"))
                self.table.setItem(0, 1, QTableWidgetItem("Opening Balance"))
                self.table.setItem(0, 2, QTableWidgetItem("-"))
                self.table.setItem(0, 3, QTableWidgetItem("-"))
                self.table.setItem(0, 4, QTableWidgetItem("-"))
                self.table.setItem(0, 5, QTableWidgetItem(f"{running_balance:,.2f}"))
                self.table.setItem(0, 6, QTableWidgetItem("")) # No actions for opening balance

                # Transactions
                # Order by transaction_date, then created_at
                ledgers = session.query(VendorLedger).filter(
                    VendorLedger.vendor_id == self.vendor_id
                ).order_by(VendorLedger.transaction_date.asc(), VendorLedger.created_at.asc()).all()

                row = 1
                for ledger in ledgers:
                    debit = float(ledger.debit or 0)
                    credit = float(ledger.credit or 0)
                    
                    # For vendors: Balance = Opening + Credit(Bills) - Debit(Payments)
                    # i.e., how much we owe them.
                    running_balance = running_balance + credit - debit
                    
                    self.table.insertRow(row)
                    self.table.setItem(row, 0, QTableWidgetItem(ledger.transaction_date.strftime("%Y-%m-%d") if ledger.transaction_date else ""))
                    self.table.setItem(row, 1, QTableWidgetItem(ledger.description or ""))
                    self.table.setItem(row, 2, QTableWidgetItem(ledger.reference_booking_id or ""))
                    self.table.setItem(row, 3, QTableWidgetItem(f"{debit:,.2f}"))
                    self.table.setItem(row, 4, QTableWidgetItem(f"{credit:,.2f}"))
                    
                    bal_item = QTableWidgetItem(f"{running_balance:,.2f}")
                    if running_balance > 0:
                        bal_item.setForeground(Qt.GlobalColor.red) # We owe them
                    elif running_balance < 0:
                        bal_item.setForeground(Qt.GlobalColor.green) # They owe us
                    self.table.setItem(row, 5, bal_item)
                    
                    # Actions Column
                    btn_edit = QPushButton("Edit")
                    btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
                    btn_edit.setStyleSheet("padding: 4px; background-color: #3b82f6; color: white; border-radius: 4px; font-weight: bold;")
                    btn_edit.clicked.connect(lambda checked, tid=ledger.id: self.edit_transaction(tid))
                    
                    action_widget = QWidget()
                    action_layout = QHBoxLayout(action_widget)
                    action_layout.setContentsMargins(0, 0, 0, 0)
                    action_layout.addWidget(btn_edit)
                    
                    self.table.setCellWidget(row, 6, action_widget)
                    
                    row += 1

                if running_balance > 0:
                    self.lbl_balance.setText(f"Payable (We Owe): PKR {running_balance:,.2f}")
                    self.lbl_balance.setStyleSheet("font-size: 16px; font-weight: bold; color: #ef4444;")
                elif running_balance < 0:
                    self.lbl_balance.setText(f"Advance (They Owe Us): PKR {abs(running_balance):,.2f}")
                    self.lbl_balance.setStyleSheet("font-size: 16px; font-weight: bold; color: #4CAF50;")
                else:
                    self.lbl_balance.setText("Balance: PKR 0.00")
                    self.lbl_balance.setStyleSheet("font-size: 16px; font-weight: bold; color: #A0AEC0;")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load ledger: {e}")

    def edit_profile(self):
        try:
            with get_session() as session:
                vendor = session.get(Vendor, self.vendor_id)
                if vendor:
                    dialog = VendorForm(item=vendor, parent=self)
                    if dialog.exec():
                        self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open edit profile: {e}")

    def add_bill(self):
        dialog = VendorAddBillDialog(self.vendor_id, self)
        if dialog.exec():
            self.load_data()

    def make_payment(self):
        dialog = VendorMakePaymentDialog(self.vendor_id, self)
        if dialog.exec():
            self.load_data()

    def export_pdf(self):
        dialog = VendorExportDialog(self.vendor_id, self)
        dialog.exec()
        
    def edit_transaction(self, transaction_id):
        dialog = VendorEditTransactionDialog(transaction_id, self)
        if dialog.exec():
            self.load_data()
