from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                               QLineEdit, QLabel, QRadioButton, QDateEdit)
from PySide6.QtCore import Qt, QDate
from ui.components.searchable_combo_box import SearchableComboBox
from repositories.customer_repository import CustomerRepository # type: ignore

class PaxWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.customer_repo = CustomerRepository()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header Row: Group Leader Toggle & Linked Customer Search
        header_layout = QHBoxLayout()
        self.group_leader_btn = QRadioButton("★ Group Leader")
        self.group_leader_btn.setStyleSheet("font-weight: bold; color: #D4AF37;") # Sleek Gold Star Indicator
        
        self.customer_search = SearchableComboBox()
        self.customer_search.search_input.setPlaceholderText("Search existing customer...")
        self.customer_search.item_selected.connect(self.auto_fill_customer)
        
        header_layout.addWidget(self.group_leader_btn)
        header_layout.addWidget(QLabel("Link to Profile:"))
        header_layout.addWidget(self.customer_search)
        
        # Detail Row: Forms
        detail_layout = QHBoxLayout()
        self.first_name_input = QLineEdit()
        self.first_name_input.setPlaceholderText("First Name")
        
        self.last_name_input = QLineEdit()
        self.last_name_input.setPlaceholderText("Last Name")
        
        self.passport_input = QLineEdit()
        self.passport_input.setPlaceholderText("Passport Number")
        
        self.cnic_input = QLineEdit()
        self.cnic_input.setPlaceholderText("CNIC")
        
        self.dob_input = QDateEdit()
        self.dob_input.setCalendarPopup(True)
        self.dob_input.setDisplayFormat("yyyy-MM-dd")
        
        detail_layout.addWidget(self.first_name_input)
        detail_layout.addWidget(self.last_name_input)
        detail_layout.addWidget(self.passport_input)
        detail_layout.addWidget(self.cnic_input)
        detail_layout.addWidget(self.dob_input)
        
        layout.addLayout(header_layout)
        layout.addLayout(detail_layout)
        self.setStyleSheet("PaxWidget { border: 1px solid #ccc; border-radius: 5px; padding: 10px; }")

    def auto_fill_customer(self, customer_id):
        customer = self.customer_repo.get_by_id(customer_id)
        if customer:
            self.first_name_input.setText(customer.first_name)
            self.last_name_input.setText(customer.last_name)
            self.passport_input.setText(customer.passport_number or "")
            self.cnic_input.setText(customer.cnic or "")
            if customer.date_of_birth:
                self.dob_input.setDate(QDate(customer.date_of_birth.year, 
                                             customer.date_of_birth.month, 
                                             customer.date_of_birth.day))
