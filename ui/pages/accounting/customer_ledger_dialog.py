import datetime
import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QTableWidget, QTableWidgetItem, QPushButton, 
                               QHeaderView, QMessageBox, QWidget, QAbstractItemView)
from PySide6.QtCore import Qt, QDate
from config.database import get_session
from models.customer import Customer
from utils.formatters import format_currency, format_date

class CustomerLedgerDialog(QDialog):
    def __init__(self, customer_id: str, viewmodel, parent=None):
        super().__init__(parent)
        self.customer_id = customer_id
        self.viewmodel = viewmodel
        self.customer = None
        self.ledger_entries = []
        self.total_balance = 0.0
        
        self.setWindowTitle("Customer Ledger")
        self.setMinimumSize(1150, 700)
        self.resize(1150, 700)
        
        self._setup_ui()
        self._connect_signals()
        self.load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()
        self.lbl_title = QLabel("Ledger: Loading...")
        self.lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        
        self.lbl_balance = QLabel("Balance: Rs. 0.00")
        self.lbl_balance.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        header_layout.addWidget(self.lbl_title)
        header_layout.addStretch()
        header_layout.addWidget(self.lbl_balance)
        layout.addLayout(header_layout)

        # Toolbar
        toolbar = QHBoxLayout()
        btn_export = QPushButton("Export PDF")
        btn_export.setObjectName("btn_secondary")
        btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_export.clicked.connect(self.export_pdf)
        toolbar.addWidget(btn_export)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Table
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "Date", "Type", "Ref Number", "Debit (Billed)", "Credit (Paid)", "Balance"
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        
    def _connect_signals(self):
        self.viewmodel.customer_ledger_loaded.connect(self._on_ledger_loaded)
        
    def load_data(self):
        with get_session() as session:
            self.customer = session.get(Customer, self.customer_id)
            if not self.customer:
                QMessageBox.warning(self, "Error", "Customer not found.")
                self.reject()
                return
            self.lbl_title.setText(f"Ledger: {self.customer.full_name} ({self.customer.customer_code})")
            
        self.viewmodel.load_customer_ledger(self.customer_id)
        
    def _on_ledger_loaded(self, ledger):
        self.ledger_entries = ledger
        self.table.setRowCount(0)
        
        balance = 0.0
        for row, tx in enumerate(ledger):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(format_date(tx["date"])))
            self.table.setItem(row, 1, QTableWidgetItem(tx["type"]))
            self.table.setItem(row, 2, QTableWidgetItem(tx["reference"]))
            
            debit_item = QTableWidgetItem(format_currency(tx["debit"]) if tx["debit"] > 0 else "-")
            if tx["debit"] > 0:
                debit_item.setForeground(Qt.GlobalColor.red)
            self.table.setItem(row, 3, debit_item)
            
            credit_item = QTableWidgetItem(format_currency(tx["credit"]) if tx["credit"] > 0 else "-")
            if tx["credit"] > 0:
                credit_item.setForeground(Qt.GlobalColor.green)
            self.table.setItem(row, 4, credit_item)
            
            bal_item = QTableWidgetItem(format_currency(tx["balance"]))
            if tx["balance"] > 0:
                bal_item.setForeground(Qt.GlobalColor.red)
            else:
                bal_item.setForeground(Qt.GlobalColor.green)
            self.table.setItem(row, 5, bal_item)
            
            balance = tx["balance"]
            
        self.total_balance = balance
        self.lbl_balance.setText(f"Balance (They Owe): {format_currency(balance)}")
        if balance > 0:
            self.lbl_balance.setStyleSheet("font-size: 18px; font-weight: bold; color: #EF4444;") # red
        else:
            self.lbl_balance.setStyleSheet("font-size: 18px; font-weight: bold; color: #10B981;") # green

    def export_pdf(self):
        if not self.customer:
            return
            
        try:
            from services.pdf_service import PDFService
            
            pdf_service = PDFService()
            filename = pdf_service.generate_customer_statement(
                customer=self.customer, 
                statement_entries=self.ledger_entries, 
                balance_due=self.total_balance
            )
            
            if os.path.exists(filename):
                os.startfile(filename)
            else:
                QMessageBox.warning(self, "Export Error", "File generated but could not be found.")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export PDF: {str(e)}")
