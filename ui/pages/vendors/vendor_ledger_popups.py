from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDoubleSpinBox,
    QDateEdit, QDialogButtonBox, QMessageBox, QComboBox, QCheckBox
)
from PySide6.QtCore import QDate
from config.database import get_session
from models.vendor import VendorLedger, Vendor
import os
import sys

class VendorAddBillDialog(QDialog):
    def __init__(self, vendor_id: str, parent=None):
        super().__init__(parent)
        self.vendor_id = vendor_id
        self.setWindowTitle("Add Bill (Credit)")
        self.setMinimumWidth(350)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("Description")
        self.ref_edit = QLineEdit()
        self.ref_edit.setPlaceholderText("Ref Booking / Invoice No")
        self.amount_edit = QDoubleSpinBox()
        self.amount_edit.setMaximum(100000000)

        form.addRow("Date:", self.date_edit)
        form.addRow("Description:", self.desc_edit)
        form.addRow("Ref Booking:", self.ref_edit)
        form.addRow("Amount (Credit):", self.amount_edit)

        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.save_bill)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def save_bill(self):
        amount = self.amount_edit.value()
        if amount <= 0:
            QMessageBox.warning(self, "Validation", "Amount must be greater than zero.")
            return

        desc = self.desc_edit.text().strip() or "Bill Received"
        ref = self.ref_edit.text().strip()

        try:
            with get_session() as session:
                ledger = VendorLedger(
                    vendor_id=self.vendor_id,
                    transaction_date=self.date_edit.date().toPython(),
                    description=desc,
                    reference_booking_id=ref,
                    debit=0,
                    credit=amount
                )
                session.add(ledger)
                session.commit()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save bill: {e}")

class VendorMakePaymentDialog(QDialog):
    def __init__(self, vendor_id: str, parent=None):
        super().__init__(parent)
        self.vendor_id = vendor_id
        self.setWindowTitle("Make Payment (Debit)")
        self.setMinimumWidth(350)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("Payment Description")
        
        self.f_payment_source = QComboBox()
        self.f_payment_source.addItems(["Select Payment Source...", "Cash Drawer", "Main Bank Account"])
        
        self.ref_edit = QLineEdit()
        self.ref_edit.setPlaceholderText("Cheque / Transfer Ref")
        self.amount_edit = QDoubleSpinBox()
        self.amount_edit.setMaximum(100000000)

        form.addRow("Date:", self.date_edit)
        form.addRow("Payment Source:", self.f_payment_source)
        form.addRow("Description:", self.desc_edit)
        form.addRow("Reference:", self.ref_edit)
        form.addRow("Amount (Debit):", self.amount_edit)

        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.save_payment)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def save_payment(self):
        amount = self.amount_edit.value()
        if amount <= 0:
            QMessageBox.warning(self, "Validation", "Amount must be greater than zero.")
            return

        if self.f_payment_source.currentIndex() == 0:
            QMessageBox.warning(self, "Validation", "Please select a Payment Source.")
            return

        desc = self.desc_edit.text().strip() or "Payment Made"
        ref = self.ref_edit.text().strip()

        try:
            with get_session() as session:
                ledger = VendorLedger(
                    vendor_id=self.vendor_id,
                    transaction_date=self.date_edit.date().toPython(),
                    description=desc,
                    reference_booking_id=ref,
                    payment_source=self.f_payment_source.currentText(),
                    debit=amount,
                    credit=0
                )
                session.add(ledger)
                session.commit()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save payment: {e}")

class VendorEditTransactionDialog(QDialog):
    def __init__(self, transaction_id: str, parent=None):
        super().__init__(parent)
        self.transaction_id = transaction_id
        self.setWindowTitle("Edit Transaction")
        self.setMinimumWidth(350)
        self._setup_ui()
        self.load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Bill (Credit)", "Payment (Debit)"])
        
        self.desc_edit = QLineEdit()
        self.ref_edit = QLineEdit()
        self.amount_edit = QDoubleSpinBox()
        self.amount_edit.setMaximum(100000000)

        form.addRow("Date:", self.date_edit)
        form.addRow("Type:", self.type_combo)
        form.addRow("Description:", self.desc_edit)
        form.addRow("Reference:", self.ref_edit)
        form.addRow("Amount:", self.amount_edit)

        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.save_changes)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def load_data(self):
        with get_session() as session:
            ledger = session.get(VendorLedger, self.transaction_id)
            if ledger:
                if ledger.transaction_date:
                    self.date_edit.setDate(QDate(ledger.transaction_date.year, ledger.transaction_date.month, ledger.transaction_date.day))
                self.desc_edit.setText(ledger.description or "")
                self.ref_edit.setText(ledger.reference_booking_id or "")
                
                debit = float(ledger.debit or 0)
                credit = float(ledger.credit or 0)
                if debit > 0:
                    self.type_combo.setCurrentIndex(1) # Payment
                    self.amount_edit.setValue(debit)
                else:
                    self.type_combo.setCurrentIndex(0) # Bill
                    self.amount_edit.setValue(credit)

    def save_changes(self):
        amount = self.amount_edit.value()
        is_payment = self.type_combo.currentIndex() == 1

        try:
            with get_session() as session:
                ledger = session.get(VendorLedger, self.transaction_id)
                if ledger:
                    ledger.transaction_date = self.date_edit.date().toPython()
                    ledger.description = self.desc_edit.text().strip()
                    ledger.reference_booking_id = self.ref_edit.text().strip()
                    ledger.debit = amount if is_payment else 0
                    ledger.credit = 0 if is_payment else amount
                session.commit()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to edit transaction: {e}")

class VendorExportDialog(QDialog):
    def __init__(self, vendor_id: str, parent=None):
        super().__init__(parent)
        self.vendor_id = vendor_id
        self.setWindowTitle("Export Ledger PDF")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.all_time_cb = QCheckBox("Export All Time")
        self.all_time_cb.setChecked(True)
        self.all_time_cb.stateChanged.connect(self._toggle_dates)
        
        form = QFormLayout()
        self.start_date = QDateEdit(QDate.currentDate().addDays(-30))
        self.start_date.setCalendarPopup(True)
        self.end_date = QDateEdit(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        
        form.addRow("Start Date:", self.start_date)
        form.addRow("End Date:", self.end_date)
        
        self._toggle_dates()
        
        layout.addWidget(self.all_time_cb)
        layout.addLayout(form)
        
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.export)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _toggle_dates(self):
        enabled = not self.all_time_cb.isChecked()
        self.start_date.setEnabled(enabled)
        self.end_date.setEnabled(enabled)

    def export(self):
        try:
            with get_session() as session:
                vendor = session.get(Vendor, self.vendor_id)
                if not vendor: return
                
                query = session.query(VendorLedger).filter(VendorLedger.vendor_id == self.vendor_id)
                
                start_str, end_str = None, None
                if not self.all_time_cb.isChecked():
                    query = query.filter(VendorLedger.transaction_date >= self.start_date.date().toPython())
                    query = query.filter(VendorLedger.transaction_date <= self.end_date.date().toPython())
                    start_str = self.start_date.date().toString("yyyy-MM-dd")
                    end_str = self.end_date.date().toString("yyyy-MM-dd")
                    
                ledgers = query.order_by(VendorLedger.transaction_date.asc(), VendorLedger.created_at.asc()).all()
                
                entries = []
                running_balance = float(vendor.opening_balance or 0)
                if self.all_time_cb.isChecked() or (ledgers and ledgers[0].transaction_date == self.start_date.date().toPython()):
                    pass
                else:
                    # we need opening balance as of start date
                    past = session.query(VendorLedger).filter(
                        VendorLedger.vendor_id == self.vendor_id, 
                        VendorLedger.transaction_date < self.start_date.date().toPython()
                    ).all()
                    for l in past:
                        running_balance += float(l.credit or 0) - float(l.debit or 0)
                
                entries.append({
                    "date": start_str or "Beginning",
                    "description": "Opening Balance",
                    "reference": "-",
                    "debit": 0,
                    "credit": 0,
                    "balance": running_balance
                })
                
                for ledger in ledgers:
                    debit = float(ledger.debit or 0)
                    credit = float(ledger.credit or 0)
                    running_balance += (credit - debit)
                    entries.append({
                        "date": ledger.transaction_date,
                        "description": ledger.description or "",
                        "reference": ledger.reference_booking_id or "",
                        "debit": debit,
                        "credit": credit
                    })
                
                from services.pdf_service import PDFService
                pdf = PDFService()
                import subprocess
                path = pdf.generate_vendor_ledger_pdf(vendor, entries, running_balance, start_str, end_str)
                QMessageBox.information(self, "Success", f"PDF exported to {path}")
                if os.name == 'nt':
                    os.startfile(path)
                elif sys.platform == 'darwin':
                    subprocess.call(['open', path])
                else:
                    subprocess.call(['xdg-open', path])
                    
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export PDF: {e}")
