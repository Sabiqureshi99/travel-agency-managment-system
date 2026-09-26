from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QLineEdit, QComboBox, QGroupBox, 
                               QDateEdit, QTimeEdit, QTableWidget, QHeaderView, 
                               QMessageBox, QFormLayout, QTextEdit, QScrollArea, QWidget)
from PySide6.QtCore import QDate, QTime, Qt
from utils.formatters import format_currency
from ui.components.searchable_combo_box import SearchableComboBox

class VisaForm(QDialog):
    def __init__(self, viewmodel, current_user_id, application=None, parent=None):
        super().__init__(parent)
        self.viewmodel = viewmodel
        self.current_user_id = current_user_id
        self.application = application
        self.setWindowTitle("Visa Application" if not application else "Edit Visa Application")
        self.setMinimumSize(850, 700)
        
        self.viewmodel.visa_saved.connect(self._on_saved)
        self.viewmodel.form_data_loaded.connect(self._on_data_loaded)
        
        self.customer_map = {}
        
        self._apply_styles()
        self._setup_ui()
        
        # Async load
        self.customer_cb.search_input.setText("Loading customers...")
        self.customer_cb.setEnabled(False)
        self.viewmodel.load_form_data()

    def _apply_styles(self):
        # Modern Dark Theme QSS specific to this form to guarantee sizing and spacing
        self.setStyleSheet("""
            QDialog {
                background-color: #12141c;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #818CF8;
                border: 1px solid #2A2D3E;
                border-radius: 8px;
                margin-top: 24px;
                background-color: #1A1D2E;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 15px;
                padding: 0 5px;
                color: #818CF8;
            }
            QLineEdit, QComboBox, QDateEdit {
                background-color: #0B0C10;
                color: #E2E8F0;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 4px 10px;
                min-height: 36px;
                font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus {
                border: 1px solid #4F46E5;
                background-color: #1A1D2E;
            }
            QLabel {
                font-size: 13px;
                color: #C4CDE8;
            }
            QTextEdit {
                background-color: #0B0C10;
                color: #E2E8F0;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
            }
            QPushButton {
                background-color: #2A2D3E;
                color: #E2E8F0;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                min-height: 36px;
            }
            QPushButton:hover {
                background-color: #3B405A;
            }
            QPushButton#btn_primary {
                background-color: #4F46E5;
                color: white;
            }
            QPushButton#btn_primary:hover {
                background-color: #4338CA;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll Area Setup
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        self.container = QWidget()
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        # Ensure layout never squishes below min sizes
        layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetMinimumSize) 
        
        # Details Group
        g1 = QGroupBox("Application Details")
        l1 = QFormLayout(g1)
        l1.setContentsMargins(15, 25, 15, 15)
        l1.setSpacing(12)
        
        self.customer_cb = SearchableComboBox()
        self.customer_cb.search_input.setPlaceholderText("Search Customer...")
        self.country = QComboBox()
        self.country.addItems(["UAE", "Saudi Arabia", "Turkey", "UK", "USA", "Schengen"])
        self.visa_type = QComboBox()
        self.visa_type.addItems(["Tourist", "Business", "Student", "Work"])
        self.embassy = QLineEdit(placeholderText="Embassy/Consulate")
        
        self.app_date = QDateEdit(QDate.currentDate())
        self.app_date.setCalendarPopup(True)
        self.appt_date = QDateEdit(QDate.currentDate().addDays(7))
        self.appt_date.setCalendarPopup(True)
        
        self.status = QComboBox()
        self.status.addItems(["Pending", "In Process", "Approved", "Rejected"])
        self.rejection_reason = QLineEdit(placeholderText="Rejection Reason")
        self.rejection_reason.hide()
        self.status.currentTextChanged.connect(self._on_status_change)
        
        l1.addRow("Customer *:", self.customer_cb)
        l1.addRow("Country *:", self.country)
        l1.addRow("Visa Type *:", self.visa_type)
        l1.addRow("Embassy:", self.embassy)
        l1.addRow("Application Date:", self.app_date)
        l1.addRow("Appointment Date:", self.appt_date)
        l1.addRow("Status:", self.status)
        l1.addRow("Rejection Reason:", self.rejection_reason)
        
        # Financials Group
        g2 = QGroupBox("Financials")
        l2 = QFormLayout(g2)
        l2.setContentsMargins(15, 25, 15, 15)
        l2.setSpacing(12)
        
        self.embassy_fees = QLineEdit("0.0")
        self.service_charges = QLineEdit("0.0")
        self.fees_charged = QLineEdit("0.0")
        
        self.total_cost_lbl = QLabel("PKR 0.00")
        self.total_cost_lbl.setStyleSheet("font-weight: bold; font-size: 14px; color: #e74c3c; min-height: 36px;")
        
        self.profit_lbl = QLabel("PKR 0.00")
        self.profit_lbl.setStyleSheet("font-weight: bold; font-size: 14px; color: #2ecc71; min-height: 36px;")
        
        l2.addRow("Embassy Fees:", self.embassy_fees)
        l2.addRow("Service Charges:", self.service_charges)
        l2.addRow("Total Cost (Calculated):", self.total_cost_lbl)
        l2.addRow("Fees Charged to Customer:", self.fees_charged)
        l2.addRow("Profit (Calculated):", self.profit_lbl)
        
        self.embassy_fees.textChanged.connect(self._calc_financials)
        self.service_charges.textChanged.connect(self._calc_financials)
        self.fees_charged.textChanged.connect(self._calc_financials)
        
        # Row Layout for Details and Financials (Side by side if space permits, else they wrap nicely)
        top_row = QHBoxLayout()
        top_row.addWidget(g1)
        top_row.addWidget(g2)
        layout.addLayout(top_row)
        
        # Applicants Group
        g3 = QGroupBox("Applicants")
        l3 = QVBoxLayout(g3)
        l3.setContentsMargins(15, 25, 15, 15)
        l3.setSpacing(10)
        
        btn_add_app = QPushButton("+ Add Applicant")
        btn_add_app.setFixedWidth(150)
        btn_add_app.clicked.connect(self._add_applicant_row)
        
        l3.addWidget(btn_add_app, alignment=Qt.AlignmentFlag.AlignRight)
        
        self.applicants_table = QTableWidget(0, 5)
        self.applicants_table.setHorizontalHeaderLabels(["Name", "Passport", "Relation", "Status", "Actions"])
        self.applicants_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.applicants_table.verticalHeader().setVisible(False)
        self.applicants_table.setAlternatingRowColors(True)
        self.applicants_table.setMinimumHeight(200)
        l3.addWidget(self.applicants_table)
        
        layout.addWidget(g3)
        
        # Notes
        notes_lbl = QLabel("Additional Notes")
        notes_lbl.setStyleSheet("font-weight: bold; color: #818CF8; font-size: 14px; margin-top: 10px;")
        self.notes = QTextEdit()
        self.notes.setPlaceholderText("Enter any special instructions or internal notes here...")
        self.notes.setMinimumHeight(80)
        self.notes.setMaximumHeight(120)
        
        layout.addWidget(notes_lbl)
        layout.addWidget(self.notes)
        
        # Set container to scroll area
        self.scroll_area.setWidget(self.container)
        main_layout.addWidget(self.scroll_area)
        
        # Fixed Footer (outside of scroll area)
        footer = QHBoxLayout()
        footer.setContentsMargins(20, 10, 20, 20)
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setFixedWidth(120)
        
        btn_save = QPushButton("Save Visa Application")
        btn_save.setObjectName("btn_primary")
        btn_save.setShortcut("Return")
        btn_save.setFixedWidth(200)
        btn_save.setDefault(True)
        
        btn_cancel.clicked.connect(self.reject)
        btn_save.clicked.connect(self._save)
        
        footer.addStretch()
        footer.addWidget(btn_cancel)
        footer.addWidget(btn_save)
        main_layout.addLayout(footer)
        
    def _on_data_loaded(self, result):
        self.customer_cb.search_input.clear()
        customers = result.get('customers', [])
        
        self.customer_map = {c.full_name: c.id for c in customers}
        if self.customer_map:
            self.customer_cb.set_data([(c.full_name, c.id) for c in customers])
            self.customer_cb.setEnabled(True)
        else:
            self.customer_cb.search_input.setText("No customers found")
            
        if self.application:
            self._populate_fields()
            
    def _populate_fields(self):
        v = self.application
        if getattr(v, 'customer', None):
            self.customer_cb.search_input.setText(v.customer.full_name)
        self.country.setCurrentText(getattr(v, 'country', ''))
        self.visa_type.setCurrentText(getattr(v, 'visa_type', ''))
        self.embassy.setText(getattr(v, 'embassy', ''))
        
        if getattr(v, 'application_date', None):
            self.app_date.setDate(v.application_date)
        if getattr(v, 'appointment_date', None):
            self.appt_date.setDate(v.appointment_date)
            
        self.status.setCurrentText(getattr(v, 'status', ''))
        self.rejection_reason.setText(getattr(v, 'rejection_reason', '') or '')
        
        self.embassy_fees.setText(str(getattr(v, 'embassy_fees', 0)))
        self.service_charges.setText(str(getattr(v, 'service_charges', 0)))
        self.fees_charged.setText(str(getattr(v, 'fees_charged', 0)))
        
        self.notes.setPlainText(getattr(v, 'notes', '') or '')
        
        self._calc_financials()
        
        if getattr(v, 'applicants', None):
            for app in v.applicants:
                self._add_applicant_row(app)
        
    def _on_status_change(self, status):
        if status == "Rejected":
            self.rejection_reason.show()
        else:
            self.rejection_reason.hide()
            
    def _calc_financials(self):
        try:
            embassy = float(self.embassy_fees.text() or 0)
            service = float(self.service_charges.text() or 0)
            charged = float(self.fees_charged.text() or 0)
            
            cost = embassy + service
            profit = charged - cost
            
            self.total_cost_lbl.setText(format_currency(cost))
            self.profit_lbl.setText(format_currency(profit))
            
            if profit >= 0:
                self.profit_lbl.setStyleSheet("font-weight: bold; font-size: 14px; color: #2ecc71; min-height: 36px;")
            else:
                self.profit_lbl.setStyleSheet("font-weight: bold; font-size: 14px; color: #e74c3c; min-height: 36px;")
        except ValueError:
            pass

    def _add_applicant_row(self, existing_applicant=None):
        from PySide6.QtWidgets import QTableWidgetItem
        
        row = self.applicants_table.rowCount()
        self.applicants_table.insertRow(row)
        
        name_item = QTableWidgetItem(existing_applicant.full_name if existing_applicant else "")
        passport_item = QTableWidgetItem(existing_applicant.passport_number if existing_applicant else "")
        relation_item = QTableWidgetItem(existing_applicant.title if existing_applicant else "") 
        
        status_cb = QComboBox()
        status_cb.addItems(["Pending", "Approved", "Rejected"])
        if existing_applicant and existing_applicant.status:
            status_cb.setCurrentText(existing_applicant.status)
            
        btn_remove = QPushButton("Remove")
        btn_remove.setStyleSheet("color: #EF4444; background: transparent; border: none;")
        btn_remove.clicked.connect(lambda _, r=row: self._remove_applicant(r))
            
        self.applicants_table.setItem(row, 0, name_item)
        self.applicants_table.setItem(row, 1, passport_item)
        self.applicants_table.setItem(row, 2, relation_item)
        self.applicants_table.setCellWidget(row, 3, status_cb)
        self.applicants_table.setCellWidget(row, 4, btn_remove)
        
    def _remove_applicant(self, row):
        button = self.sender()
        if button and isinstance(button, QPushButton):
            index = self.applicants_table.indexAt(button.pos())
            if index.isValid():
                self.applicants_table.removeRow(index.row())

    def _save(self):
        c_name = self.customer_cb.search_input.text()
        if not c_name or not self.customer_cb.isEnabled():
            QMessageBox.warning(self, "Error", "Customer must be selected.")
            return
            
        if not self.country.currentText() or not self.visa_type.currentText():
            QMessageBox.warning(self, "Error", "Country and Visa Type are required.")
            return
            
        if self.applicants_table.rowCount() == 0:
            QMessageBox.warning(self, "Error", "At least one applicant is required.")
            return
            
        applicants = []
        for i in range(self.applicants_table.rowCount()):
            name_item = self.applicants_table.item(i, 0)
            passport_item = self.applicants_table.item(i, 1)
            relation_item = self.applicants_table.item(i, 2)
            status_widget = self.applicants_table.cellWidget(i, 3)
            
            name = name_item.text().strip() if name_item else ""
            passport = passport_item.text().strip() if passport_item else ""
            relation = relation_item.text().strip() if relation_item else ""
            status = status_widget.currentText() if isinstance(status_widget, QComboBox) else "Pending"
            
            if name and passport:
                applicants.append({
                    "full_name": name,
                    "passport_number": passport,
                    "title": relation,
                    "status": status
                })
                
        try:
            embassy_fees = float(self.embassy_fees.text() or 0)
            service_charges = float(self.service_charges.text() or 0)
            fees_charged = float(self.fees_charged.text() or 0)
        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid numeric values in Financials.")
            return
            
        total_cost = embassy_fees + service_charges
        profit = fees_charged - total_cost
        
        data = {
            "id": self.application.id if self.application else None,
            "customer_id": self.customer_map.get(c_name, ""),
            "country": self.country.currentText(),
            "visa_type": self.visa_type.currentText(),
            "embassy": self.embassy.text().strip(),
            "application_date": self.app_date.date().toPython(),
            "appointment_date": self.appt_date.date().toPython(),
            "status": self.status.currentText(),
            "rejection_reason": self.rejection_reason.text().strip(),
            "embassy_fees": embassy_fees,
            "service_charges": service_charges,
            "total_cost": total_cost,
            "fees_charged": fees_charged,
            "profit": profit,
            "notes": self.notes.toPlainText().strip()
        }
        
        self.viewmodel.save_visa(data, applicants_data=applicants, current_user_id=self.current_user_id)
        
    def _on_saved(self, result):
        try:
            from services.accounting_service import AccountingService
            from config.database import get_session
            from models.visa import VisaApplication
            from models.booking import Booking
            
            with get_session() as session:
                visa_app = session.query(VisaApplication).get(result.id)
                if visa_app:
                    central = Booking(
                        booking_type='Visa_Only',
                        customer_id=visa_app.customer_id,
                        cost_price=visa_app.total_cost,
                        selling_price=visa_app.fees_charged,
                        details=f"Visa App - Country: {visa_app.country}, Type: {visa_app.visa_type}"
                    )
                    session.add(central)
                    session.commit()
                    
                    if visa_app.fees_charged > 0:
                        invoice = AccountingService().post_standalone_booking(
                            customer_id=visa_app.customer_id,
                            total_amount=visa_app.fees_charged,
                            item_description=f"Visa Application - Country: {visa_app.country}, Type: {visa_app.visa_type}",
                            created_by=self.current_user_id
                        )
                        
                        import os
                        import datetime
                        from services.invoice_generator import InvoiceGenerator
                        from utils.pdf_generator import VoucherBuilder
                        
                        os.makedirs("invoices", exist_ok=True)
                        inv_path = os.path.abspath(f"invoices/Invoice_{invoice.invoice_number}.pdf")
                        InvoiceGenerator.generate_invoice_pdf(invoice, inv_path)
                        if hasattr(os, 'startfile'):
                            os.startfile(inv_path)
                            
                        # Generate Voucher PDF
                        customer_name = visa_app.customer.full_name if visa_app.customer else "Unknown Customer"
                        customer_passport = visa_app.customer.passport_number if visa_app.customer else ""
                        
                        v_data = {
                            'voucher_no': f"VV-{visa_app.id[:6].upper()}",
                            'issue_date': datetime.datetime.now().strftime("%d/%m/%Y"),
                            'pkg_category': 'VISA ONLY',
                            'print_dt': datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                            'branch_office': 'MAIN OFFICE',
                            'passengers': [
                                {'name': customer_name, 'passport': customer_passport, 'group': ''}
                            ],
                            'accommodation': [],
                            'transport': [],
                            'flights': [],
                            'visa': {
                                'country': visa_app.country,
                                'type': visa_app.visa_type,
                                'embassy': visa_app.embassy,
                                'applicants': len(visa_app.applicants) if visa_app.applicants else 1
                            }
                        }
                        
                        filename = f"Visa_Voucher_{visa_app.id[:8]}.pdf"
                        voucher_path = VoucherBuilder(v_data, filename=filename).generate()
                        if hasattr(os, 'startfile'):
                            os.startfile(voucher_path)

                    from core.signals import app_signals
                    if hasattr(app_signals, 'data_changed'):
                        app_signals.data_changed.emit()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save centralized booking or generate invoice/voucher: {str(e)}")
        self.accept()
