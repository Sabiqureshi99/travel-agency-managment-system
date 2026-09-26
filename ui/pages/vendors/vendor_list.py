from core.permissions import has_permission, Modules, Actions
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QComboBox, QTableWidget, 
                               QHeaderView, QMessageBox, QTableWidgetItem, QLineEdit)
from PySide6.QtCore import Qt
from ui.pages.vendors.vendor_form import VendorForm
from config.database import get_session
from repositories.vendor_repository import VendorRepository
from services.vendor_service import VendorService

class VendorListPage(QWidget):
    def __init__(self, current_user, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.current_page = 1
        self.page_size = 50
        self.total_records = 0
        
        self._setup_ui()
        self._load_data()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        header = QHBoxLayout()
        title = QLabel("Vendor Management")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.btn_add = QPushButton("Add Vendor")
        self.btn_add.setObjectName("btn_primary")
        self.btn_add.setShortcut("Return")
        self.btn_add.setEnabled(has_permission(self.current_user, Modules.VENDORS, Actions.ADD))
        self.btn_add.clicked.connect(self._on_add_vendor)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.btn_add)
        layout.addLayout(header)
        
        filters = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search company, contact...")
        self.search_input.textChanged.connect(self.on_search)
        
        self.type_cb = QComboBox()
        self.type_cb.addItems(["All", "Overall", "Airline", "Hotel", "Visa Agent", "Transport", "Other"])
        self.type_cb.currentTextChanged.connect(self.on_search)
        
        filters.addWidget(self.search_input)
        filters.addWidget(QLabel("Type:"))
        filters.addWidget(self.type_cb)
        
        self.btn_global_vendor_report = QPushButton("📄 Global Vendor Ledger")
        self.btn_global_vendor_report.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_global_vendor_report.setStyleSheet("padding: 8px; background-color: #8b5cf6; color: white; border-radius: 4px; font-weight: bold;")
        self.btn_global_vendor_report.clicked.connect(self._generate_global_vendor_summary)
        filters.addWidget(self.btn_global_vendor_report)
        
        filters.addStretch()
        layout.addLayout(filters)
        
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            "Code", "Company", "Type", "Contact", "Phone", "Email", "Status", "Actions"
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(45)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        pagination_layout = QHBoxLayout()
        pagination_layout.addStretch()
        self.btn_prev = QPushButton("< Prev")
        self.lbl_page = QLabel("Page 1 of 1")
        self.btn_next = QPushButton("Next >")
        self.btn_prev.clicked.connect(self._prev_page)
        self.btn_next.clicked.connect(self._next_page)
        pagination_layout.addWidget(self.btn_prev)
        pagination_layout.addWidget(self.lbl_page)
        pagination_layout.addWidget(self.btn_next)
        pagination_layout.addStretch()
        layout.addLayout(pagination_layout)
        
    def _load_data(self):
        self.table.setRowCount(0)
        filter_type = self.type_cb.currentText()
        search_query = self.search_input.text()
        skip = (self.current_page - 1) * self.page_size
        
        try:
            with get_session() as session:
                repo = VendorRepository(session)
                service = VendorService(repo)
                vendors, total = service.search_vendors_paginated(search_query, skip=skip, limit=self.page_size, vendor_type=filter_type)
                
                self.total_records = total
                import math
                total_pages = max(1, math.ceil(self.total_records / self.page_size))
                self.lbl_page.setText(f"Page {self.current_page} of {total_pages}")
                self.btn_prev.setEnabled(self.current_page > 1)
                self.btn_next.setEnabled(self.current_page < total_pages)
                
                self._vendors = vendors
                for r_idx, vendor in enumerate(vendors):
                    self.table.insertRow(r_idx)
                    self.table.setItem(r_idx, 0, QTableWidgetItem(vendor.vendor_code or ""))
                    self.table.setItem(r_idx, 1, QTableWidgetItem(vendor.company_name or ""))
                    self.table.setItem(r_idx, 2, QTableWidgetItem(vendor.vendor_type or ""))
                    self.table.setItem(r_idx, 3, QTableWidgetItem(vendor.contact_person or ""))
                    self.table.setItem(r_idx, 4, QTableWidgetItem(vendor.phone or ""))
                    self.table.setItem(r_idx, 5, QTableWidgetItem(vendor.email or ""))
                    self.table.setItem(r_idx, 6, QTableWidgetItem("Active"))
                    
                    # Action button
                    action_widget = QWidget()
                    action_layout = QHBoxLayout(action_widget)
                    action_layout.setContentsMargins(4, 4, 4, 4)
                    
                    ledger_btn = QPushButton("Ledger")
                    ledger_btn.setObjectName("btn_secondary")
                    ledger_btn.clicked.connect(lambda checked, idx=r_idx: self._open_ledger(idx))
                    
                    report_btn = QPushButton("📄 Global Report")
                    report_btn.setStyleSheet("padding: 4px; background-color: #8b5cf6; color: white; border-radius: 4px; font-weight: bold;")
                    report_btn.clicked.connect(lambda checked, idx=r_idx: self._generate_vendor_report(idx))
                    
                    action_layout.addWidget(ledger_btn)
                    action_layout.addWidget(report_btn)
                    action_layout.addStretch()
                    
                    self.table.setCellWidget(r_idx, 7, action_widget)
                    self.table.setRowHeight(r_idx, 50)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load vendors: {e}")
            
    def _open_ledger(self, idx):
        if not hasattr(self, '_vendors') or idx >= len(self._vendors):
            return
        vendor = self._vendors[idx]
        from ui.pages.vendors.vendor_ledger_dialog import VendorLedgerDialog
        dialog = VendorLedgerDialog(vendor.id, parent=self)
        dialog.exec()
        
    def _generate_vendor_report(self, idx):
        if not hasattr(self, '_vendors') or idx >= len(self._vendors):
            return
        vendor = self._vendors[idx]
        
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        from services.pdf_engine import GlobalPDFEngine
        from config.database import get_session
        from models.vendor import VendorLedger
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Supplier Report",
            f"Supplier_Report_{vendor.company_name}.pdf",
            "PDF Files (*.pdf)"
        )
        if not filepath:
            return
            
        try:
            transactions = []
            with get_session() as session:
                ledgers = session.query(VendorLedger).filter_by(vendor_id=vendor.id).order_by(VendorLedger.created_at).all()
                for l in ledgers:
                    tx_date = l.created_at.strftime("%Y-%m-%d") if l.created_at else "Unknown"
                    tx_type = 'Payment' if l.debit > 0 else ('Bill' if l.credit > 0 else 'Adjustment')
                    transactions.append({
                        'date': tx_date,
                        'ref': l.reference_booking_id or 'N/A',
                        'type': tx_type,
                        'source': l.payment_source if l.payment_source else 'N/A',
                        'debit': float(l.debit),
                        'credit': float(l.credit)
                    })
                    
            engine = GlobalPDFEngine()
            engine.generate_supplier_report(filepath, vendor.company_name, transactions, "All Time")
            
            QMessageBox.information(self, "Success", f"Supplier Report generated successfully:\n{filepath}")
            QDesktopServices.openUrl(QUrl.fromLocalFile(filepath))
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate report: {e}")

    def _generate_global_vendor_summary(self):
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        from services.pdf_engine import GlobalPDFEngine
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Global Vendor Ledger",
            "Global_Vendor_Ledger.pdf",
            "PDF Files (*.pdf)"
        )
        if not filepath:
            return
            
        try:
            from config.database import get_session
            from models.vendor import Vendor, VendorLedger
            from sqlalchemy import select, func

            with get_session() as session:
                # Fetch all active vendors
                vendors = session.scalars(
                    select(Vendor).where(Vendor.is_deleted == False).order_by(Vendor.company_name)
                ).all()

                formatted_balances = []
                for vendor in vendors:
                    # Sum credits (billed) and debits (paid) from ledger
                    billed = session.scalar(
                        select(func.coalesce(func.sum(VendorLedger.credit), 0.0))
                        .where(VendorLedger.vendor_id == vendor.id)
                    ) or 0.0
                    paid = session.scalar(
                        select(func.coalesce(func.sum(VendorLedger.debit), 0.0))
                        .where(VendorLedger.vendor_id == vendor.id)
                    ) or 0.0
                    balance = float(billed) - float(paid)

                    formatted_balances.append({
                        'code': vendor.vendor_code or '',
                        'company': vendor.company_name,
                        'type': vendor.vendor_type if vendor.vendor_type else 'N/A',
                        'billed': float(billed),
                        'paid': float(paid),
                        'balance': balance
                    })

            engine = GlobalPDFEngine()
            engine.generate_global_supplier_summary(filepath, formatted_balances, "All Time")

            QMessageBox.information(self, "Success", f"Global Vendor Ledger generated successfully:\n{filepath}")
            QDesktopServices.openUrl(QUrl.fromLocalFile(filepath))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate global report: {e}")
            
    def refresh(self):
        self._load_data()
        
    def on_search(self):
        self.current_page = 1
        self.refresh()
        
    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._load_data()
            
    def _next_page(self):
        import math
        total_pages = max(1, math.ceil(self.total_records / self.page_size))
        if self.current_page < total_pages:
            self.current_page += 1
            self._load_data()
        
    def _on_add_vendor(self):
        form = VendorForm(parent=self)
        if form.exec():
            # Data is saved in the form's accept method
            self.refresh()
