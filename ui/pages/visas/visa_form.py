from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QLineEdit, QFormLayout, QComboBox, 
                               QDateEdit, QMessageBox, QGroupBox)
from PySide6.QtCore import Qt, QDate
from viewmodels.visa_viewmodel import VisaViewModel
from services.customer_service import CustomerService

class VisaFormDialog(QDialog):
    def __init__(self, parent=None, visa=None, current_user_id="system"):
        super().__init__(parent)
        self.visa = visa
        self.current_user_id = current_user_id
        self.viewmodel = VisaViewModel()
        self.viewmodel.visa_saved.connect(self._on_saved)
        self.viewmodel.error_occurred.connect(self._on_error)
        self.init_ui()
        if self.visa:
            self.load_data()

    def init_ui(self):
        self.setWindowTitle("Visa Application" if not self.visa else "Edit Visa Application")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # Form Layout
        form_group = QGroupBox("Application Details")
        form_layout = QFormLayout()
        
        self.customer_cb = QComboBox()
        form_layout.addRow("Customer *:", self.customer_cb)
        
        self.country_input = QLineEdit()
        form_layout.addRow("Country *:", self.country_input)
        
        self.visa_type_cb = QComboBox()
        self.visa_type_cb.addItems(["Tourist", "Business", "Student", "Work", "Transit"])
        form_layout.addRow("Visa Type *:", self.visa_type_cb)
        
        self.status_cb = QComboBox()
        self.status_cb.addItems(["Pending", "Applied", "In Process", "Approved", "Rejected", "Expired"])
        form_layout.addRow("Status:", self.status_cb)
        
        self.app_date = QDateEdit()
        self.app_date.setCalendarPopup(True)
        self.app_date.setDate(QDate.currentDate())
        form_layout.addRow("Application Date *:", self.app_date)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Financials
        fin_group = QGroupBox("Financials")
        fin_layout = QFormLayout()
        self.total_cost_input = QLineEdit()
        self.total_cost_input.setText("0")
        fin_layout.addRow("Total Cost:", self.total_cost_input)
        fin_group.setLayout(fin_layout)
        layout.addWidget(fin_group)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("Save")
        self.btn_save.setShortcut("Return")
        self.btn_save.clicked.connect(self._on_save)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)
        
        self._populate_customers()

    def _populate_customers(self):
        try:
            customers = CustomerService().search_customers(limit=1000)
            self.customer_map = {c.full_name: c.id for c in customers}
            self.customer_cb.addItems(list(self.customer_map.keys()))
        except Exception as e:
            pass

    def load_data(self):
        # Setting combobox text works if name matches, but usually we just leave it for editing
        # or implement a proper reverse lookup from customer_id to full_name.
        self.country_input.setText(getattr(self.visa, 'country', ''))
        self.visa_type_cb.setCurrentText(getattr(self.visa, 'visa_type', 'Tourist'))
        self.status_cb.setCurrentText(getattr(self.visa, 'status', 'Applied'))
        
        d_date = getattr(self.visa, 'application_date', None)
        if d_date:
            self.app_date.setDate(d_date)
            
        self.total_cost_input.setText(str(getattr(self.visa, 'total_cost', 0)))

    def _on_save(self):
        customer_name = self.customer_cb.currentText()
        if not customer_name:
            QMessageBox.warning(self, "Error", "Please select a customer.")
            return
            
        customer_id = self.customer_map.get(customer_name, None)
        
        data = {
            'customer_id': customer_id,
            'country': self.country_input.text().strip(),
            'visa_type': self.visa_type_cb.currentText(),
            'status': self.status_cb.currentText(),
            'application_date': self.app_date.date().toPython(),
            'total_cost': float(self.total_cost_input.text() or 0)
        }
        
        if self.visa:
            data['id'] = self.visa.id
            
        self.viewmodel.save_visa(data, applicants_data=[], current_user_id=self.current_user_id)
        self.btn_save.setEnabled(False)

    def _on_saved(self, result):
        self.accept()

    def _on_error(self, message):
        self.btn_save.setEnabled(True)
        QMessageBox.critical(self, "Error", message)
