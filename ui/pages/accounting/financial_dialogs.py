from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QHBoxLayout, 
                               QPushButton, QLineEdit, QDateEdit, QComboBox, 
                               QTextEdit, QMessageBox, QDoubleSpinBox, QLabel)
from PySide6.QtCore import QDate, Qt
import uuid
from config.database import get_session
from models.accounting import Expense, VendorPayment, Withdrawal, InternalTransfer, PaymentSource
from models.vendor import Vendor

class ExpenseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Log Expense")
        self.setMinimumWidth(400)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        self.f_date = QDateEdit(QDate.currentDate())
        self.f_date.setCalendarPopup(True)
        
        self.f_category = QComboBox()
        self.f_category.addItems(["Office Rent", "Utilities", "Salaries", "Marketing", "Maintenance", "Misc"])
        self.f_category.setEditable(True)
        
        self.f_payment_source = QComboBox()
        self.f_payment_source.addItems([PaymentSource.CASH.value, PaymentSource.BANK.value])
        
        self.bank_name_input = QLineEdit()
        self.bank_name_input.setPlaceholderText("Bank Name (if Bank selected)")
        self.bank_name_input.setVisible(False)
        self.f_payment_source.currentTextChanged.connect(
            lambda t: self.bank_name_input.setVisible(t == PaymentSource.BANK.value)
        )
        
        self.f_amount = QDoubleSpinBox()
        self.f_amount.setMaximum(100000000)
        
        self.f_desc = QTextEdit()
        self.f_desc.setMaximumHeight(80)
        
        form_layout.addRow("Date:", self.f_date)
        form_layout.addRow("Category:", self.f_category)
        form_layout.addRow("Payment Source:", self.f_payment_source)
        form_layout.addRow("", self.bank_name_input)
        form_layout.addRow("Amount (PKR):", self.f_amount)
        form_layout.addRow("Description:", self.f_desc)
        
        layout.addLayout(form_layout)
        
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Save Expense")
        btn_save.setObjectName("btn_primary")
        btn_save.setShortcut("Return")
        btn_save.clicked.connect(self.save_expense)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
        
    def save_expense(self):
        if self.f_amount.value() <= 0:
            QMessageBox.warning(self, "Validation Error", "Amount must be greater than 0.")
            return
            
        source = PaymentSource.CASH if self.f_payment_source.currentText() == PaymentSource.CASH.value else PaymentSource.BANK
        bank_name = self.bank_name_input.text() if source == PaymentSource.BANK else None
        
        if source == PaymentSource.BANK and not bank_name:
            QMessageBox.warning(self, "Validation Error", "Bank Name is required for Bank payments.")
            return
            
        try:
            from models.accounting import ChartOfAccount
            with get_session() as session:
                category_name = self.f_category.currentText()
                account = session.query(ChartOfAccount).filter_by(account_name=category_name).first()
                if not account:
                    account = ChartOfAccount(
                        account_code=f"EXP-{uuid.uuid4().hex[:4].upper()}",
                        account_name=category_name,
                        account_type="Expense",
                        is_leaf=True
                    )
                    session.add(account)
                    session.flush()

                exp = Expense(
                    expense_number=f"EXP-{uuid.uuid4().hex[:6].upper()}",
                    expense_date=self.f_date.date().toPython(),
                    account_id=account.id,
                    payment_method=self.f_payment_source.currentText(),
                    payment_source=source,
                    bank_account_name=bank_name,
                    amount=self.f_amount.value(),
                    description=self.f_desc.toPlainText()
                )
                session.add(exp)
                session.commit()
            QMessageBox.information(self, "Success", "Expense logged successfully.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save expense: {str(e)}")

class VendorPaymentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Log Vendor Payment")
        self.setMinimumWidth(400)
        self.setup_ui()
        self.load_vendors()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        self.f_date = QDateEdit(QDate.currentDate())
        self.f_date.setCalendarPopup(True)
        
        self.f_vendor = QComboBox()
        self.f_vendor.setEditable(True)
        
        self.f_amount = QDoubleSpinBox()
        self.f_amount.setMaximum(100000000)
        
        self.f_method = QComboBox()
        self.f_method.addItems(["Bank Transfer", "Cash", "Cheque"])
        
        self.f_ref = QTextEdit()
        self.f_ref.setPlaceholderText("Reference number or details...")
        self.f_ref.setMaximumHeight(80)
        
        form_layout.addRow("Date:", self.f_date)
        form_layout.addRow("Vendor/Vendor:", self.f_vendor)
        form_layout.addRow("Amount (PKR):", self.f_amount)
        form_layout.addRow("Payment Method:", self.f_method)
        form_layout.addRow("Reference:", self.f_ref)
        
        layout.addLayout(form_layout)
        
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Save Payment")
        btn_save.setObjectName("btn_primary")
        btn_save.setShortcut("Return")
        btn_save.clicked.connect(self.save_payment)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
        
    def load_vendors(self):
        self.f_vendor.addItem("Manual Entry...", None)
        try:
            with get_session() as session:
                sups = session.query(Vendor).all()
                for s in sups:
                    self.f_vendor.addItem(s.company_name, s.id)
        except Exception:
            pass

    def save_payment(self):
        if self.f_amount.value() <= 0:
            QMessageBox.warning(self, "Validation Error", "Amount must be greater than 0.")
            return
            
        sup_id = self.f_vendor.currentData()
        sup_name = self.f_vendor.currentText()
        if not sup_id:
            sup_name = self.f_vendor.currentText()
            
        try:
            with get_session() as session:
                vp = VendorPayment(
                    payment_number=f"VP-{uuid.uuid4().hex[:6].upper()}",
                    date=self.f_date.date().toPython(),
                    vendor_id=sup_id,
                    vendor_name=sup_name,
                    amount=self.f_amount.value(),
                    payment_method=self.f_method.currentText(),
                    reference_details=self.f_ref.toPlainText()
                )
                session.add(vp)
                session.commit()
            QMessageBox.information(self, "Success", "Vendor Payment logged successfully.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save payment: {str(e)}")


class WithdrawalDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Log Owner Withdrawal")
        self.setMinimumWidth(400)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        self.f_date = QDateEdit(QDate.currentDate())
        self.f_date.setCalendarPopup(True)
        
        self.f_amount = QDoubleSpinBox()
        self.f_amount.setMaximum(100000000)
        
        self.f_desc = QTextEdit()
        self.f_desc.setMaximumHeight(80)
        
        form_layout.addRow("Date:", self.f_date)
        form_layout.addRow("Amount (PKR):", self.f_amount)
        form_layout.addRow("Description:", self.f_desc)
        
        layout.addLayout(form_layout)
        
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Save Withdrawal")
        btn_save.setObjectName("btn_primary")
        btn_save.setShortcut("Return")
        btn_save.clicked.connect(self.save_withdrawal)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
        
    def save_withdrawal(self):
        if self.f_amount.value() <= 0:
            QMessageBox.warning(self, "Validation Error", "Amount must be greater than 0.")
            return
            
        try:
            with get_session() as session:
                w = Withdrawal(
                    withdrawal_number=f"WD-{uuid.uuid4().hex[:6].upper()}",
                    date=self.f_date.date().toPython(),
                    amount=self.f_amount.value(),
                    description=self.f_desc.toPlainText()
                )
                session.add(w)
                session.commit()
            QMessageBox.information(self, "Success", "Withdrawal logged successfully.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save withdrawal: {str(e)}")


class InternalTransferDialog(QDialog):
    def __init__(self, available_cash: float, parent=None):
        super().__init__(parent)
        self.available_cash = available_cash
        self.setWindowTitle("Transfer Cash to Bank")
        self.setFixedSize(400, 300)
        self.setStyleSheet("QDialog { background-color: #0F172A; } QLabel { color: #F8FAFC; }")

        layout = QFormLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        # Info Header
        info_lbl = QLabel(f"Available Cash in Drawer: Rs. {self.available_cash:,.2f}")
        info_lbl.setStyleSheet("color: #10B981; font-weight: bold;")
        layout.addRow(info_lbl)

        # Form Fields
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0.01, self.available_cash if self.available_cash > 0 else 99999999.99)
        self.amount_input.setDecimals(2)
        self.amount_input.setPrefix("Rs. ")
        self.amount_input.setStyleSheet("padding: 8px; font-size: 14px;")

        self.bank_input = QComboBox()
        self.bank_input.addItems(["Meezan Bank", "NayaPay", "Allied Bank"])
        self.bank_input.setEditable(True)
        self.bank_input.setStyleSheet("padding: 8px; font-size: 14px;")

        self.note_input = QLineEdit()
        self.note_input.setPlaceholderText("e.g. End of day deposit")
        self.note_input.setStyleSheet("padding: 8px; font-size: 14px;")

        layout.addRow("Transfer Amount:*", self.amount_input)
        layout.addRow("Destination Bank:*", self.bank_input)
        layout.addRow("Reference Note:", self.note_input)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_submit = QPushButton("Confirm Transfer")
        btn_submit.setStyleSheet("background-color: #3B82F6; color: white; padding: 10px; border-radius: 5px;")
        btn_submit.clicked.connect(self.process_transfer)
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_submit)
        layout.addRow(btn_layout)

    def process_transfer(self):
        amt = self.amount_input.value()
        if amt <= 0:
            QMessageBox.warning(self, "Invalid Amount", "Please enter a transfer amount greater than zero.")
            return
        if amt > self.available_cash:
            QMessageBox.warning(
                self, "Insufficient Cash",
                f"Transfer amount (Rs. {amt:,.2f}) exceeds available cash in drawer (Rs. {self.available_cash:,.2f})."
            )
            return

        bank_name = self.bank_input.currentText().strip()
        if not bank_name:
            QMessageBox.warning(self, "Invalid Bank", "Please specify a destination bank.")
            return

        try:
            with get_session() as session:
                transfer = InternalTransfer(
                    transfer_date=QDate.currentDate().toPython(),
                    amount=amt,
                    source=PaymentSource.CASH.value,
                    destination=PaymentSource.BANK.value,
                    destination_bank_account=bank_name,
                    reference_note=self.note_input.text().strip() or None
                )
                session.add(transfer)
                session.commit()
                # #region agent log
                try:
                    import json, time
                    open(r"E:\Customized Travel Agency System\debug-5da8ec.log", "a", encoding="utf-8").write(json.dumps({"sessionId":"5da8ec","hypothesisId":"A","location":"financial_dialogs.py:process_transfer","message":"internal transfer saved","data":{"transfer_id": str(transfer.id),"transfer_date": str(transfer.transfer_date),"amount": float(amt),"bank": bank_name},"timestamp":int(time.time()*1000)})+"\n")
                except Exception:
                    pass
                # #endregion

            QMessageBox.information(
                self, "Transfer Successful",
                f"\u2705 Rs. {amt:,.2f} transferred from Cash Drawer \u2192 {bank_name}.\n\n"
                f"Cash balance reduced and bank balance updated."
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Transfer failed: {str(e)}")

