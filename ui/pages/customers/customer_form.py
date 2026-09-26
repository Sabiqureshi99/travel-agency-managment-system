from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QLineEdit, QComboBox, QTabWidget, 
                               QWidget, QDateEdit, QTextEdit, QCheckBox, 
                               QTableWidget, QHeaderView, QMessageBox, QTableWidgetItem)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QPainterPath  # must be at top level

class CustomerForm(QDialog):
    def __init__(self, customer=None, parent=None):
        super().__init__(parent)
        self.customer = customer
        self.setWindowTitle("New Customer" if not customer else f"Edit Customer: {customer.get('name', '')}")
        self.setMinimumSize(700, 500)
        self._setup_ui()
        if customer:
            self._populate_data()
            
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        
        # Tab 1: Personal Info
        tab_personal = QWidget()
        personal_layout = QVBoxLayout(tab_personal)
        
        name_layout = QHBoxLayout()
        self.title_cb = QComboBox()
        self.title_cb.addItems(["Mr", "Mrs", "Miss", "Dr"])
        self.first_name = QLineEdit()
        self.first_name.setPlaceholderText("First Name *")
        self.last_name = QLineEdit()
        self.last_name.setPlaceholderText("Last Name")
        name_layout.addWidget(self.title_cb)
        name_layout.addWidget(self.first_name)
        name_layout.addWidget(self.last_name)
        
        personal_layout.addLayout(name_layout)
        
        self.father_name = QLineEdit()
        self.father_name.setPlaceholderText("Father/Husband Name")
        personal_layout.addWidget(self.father_name)
        
        self.gender = QComboBox()
        self.gender.addItems(["Male", "Female", "Other"])
        personal_layout.addWidget(self.gender)
        
        self.dob = QDateEdit()
        self.dob.setCalendarPopup(True)
        personal_layout.addWidget(QLabel("Date of Birth:"))
        personal_layout.addWidget(self.dob)
        
        self.cust_type = QComboBox()
        self.cust_type.addItems(["Individual", "Corporate", "VIP"])
        personal_layout.addWidget(self.cust_type)
        
        self.nationality = QLineEdit()
        self.nationality.setPlaceholderText("Nationality")
        personal_layout.addWidget(self.nationality)
        
        self.tabs.addTab(tab_personal, "Personal Info")
        
        # Tab 2: Contact
        tab_contact = QWidget()
        contact_layout = QVBoxLayout(tab_contact)
        self.phone = QLineEdit()
        self.phone.setPlaceholderText("Primary Phone *")
        self.whatsapp = QLineEdit()
        self.whatsapp.setPlaceholderText("WhatsApp")
        self.email = QLineEdit()
        self.email.setPlaceholderText("Email")
        self.address = QTextEdit()
        self.address.setPlaceholderText("Address")
        self.is_vip = QCheckBox("Is VIP")
        contact_layout.addWidget(self.phone)
        contact_layout.addWidget(self.whatsapp)
        contact_layout.addWidget(self.email)
        contact_layout.addWidget(self.address)
        contact_layout.addWidget(self.is_vip)
        self.tabs.addTab(tab_contact, "Contact")
        
        # Tab 3: Passport & CNIC
        tab_docs = QWidget()
        docs_layout = QVBoxLayout(tab_docs)
        
        pass_layout = QHBoxLayout()
        self.passport = QLineEdit()
        self.passport.setPlaceholderText("Passport Number")
        
        self.btn_scan = QPushButton("📷 Upload Passport")
        self.btn_scan.setFixedWidth(120)
        self.btn_scan.setStyleSheet("background-color: #3b82f6; color: white; font-weight: bold; border-radius: 4px;")
        self.btn_scan.clicked.connect(self._open_scanner)
        
        pass_layout.addWidget(self.passport)
        pass_layout.addWidget(self.btn_scan)
        
        self.pass_expiry = QDateEdit()
        self.pass_expiry.setCalendarPopup(True)
        self.cnic = QLineEdit()
        self.cnic.setPlaceholderText("CNIC Number")
        docs_layout.addLayout(pass_layout)
        docs_layout.addWidget(QLabel("Passport Expiry:"))
        docs_layout.addWidget(self.pass_expiry)
        docs_layout.addWidget(self.cnic)
        self.tabs.addTab(tab_docs, "Passport & CNIC")
        
        # Tab 4: Family Members
        tab_family = QWidget()
        fam_layout = QVBoxLayout(tab_family)
        self.fam_table = QTableWidget(0, 3)
        self.fam_table.setHorizontalHeaderLabels(["Name", "Relation", "Age"])
        self.fam_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.btn_add_fam = QPushButton("Add Family Member")
        fam_layout.addWidget(self.btn_add_fam)
        fam_layout.addWidget(self.fam_table)
        self.tabs.addTab(tab_family, "Family")
        
        # Tab 5: Emergency Contacts
        tab_emerg = QWidget()
        emerg_layout = QVBoxLayout(tab_emerg)
        self.emerg_table = QTableWidget(0, 3)
        self.emerg_table.setHorizontalHeaderLabels(["Name", "Relation", "Phone"])
        self.emerg_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.btn_add_emerg = QPushButton("Add Emergency Contact")
        emerg_layout.addWidget(self.btn_add_emerg)
        emerg_layout.addWidget(self.emerg_table)
        self.tabs.addTab(tab_emerg, "Emergency")
        
        main_layout.addWidget(self.tabs)
        
        # Footer
        footer = QHBoxLayout()
        self.btn_save = QPushButton("Save")
        self.btn_save.setShortcut("Return")
        self.btn_save.setStyleSheet("background-color: #4F46E5; color: white;")
        self.btn_cancel = QPushButton("Cancel")
        footer.addStretch()
        footer.addWidget(self.btn_cancel)
        footer.addWidget(self.btn_save)
        main_layout.addLayout(footer)
        
        self.btn_save.clicked.connect(self._save)
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_add_fam.clicked.connect(self._add_fam_row)
        self.btn_add_emerg.clicked.connect(self._add_emerg_row)
        
    def _add_fam_row(self):
        row = self.fam_table.rowCount()
        self.fam_table.insertRow(row)
        self.fam_table.setItem(row, 0, QTableWidgetItem(""))
        self.fam_table.setItem(row, 1, QTableWidgetItem(""))
        self.fam_table.setItem(row, 2, QTableWidgetItem(""))

    def _add_emerg_row(self):
        row = self.emerg_table.rowCount()
        self.emerg_table.insertRow(row)
        self.emerg_table.setItem(row, 0, QTableWidgetItem(""))
        self.emerg_table.setItem(row, 1, QTableWidgetItem(""))
        self.emerg_table.setItem(row, 2, QTableWidgetItem(""))
        
    def _populate_data(self):
        c = self.customer
        self.title_cb.setCurrentText(c.get('title', 'Mr'))
        self.first_name.setText(c.get('first_name', ''))
        self.last_name.setText(c.get('last_name', ''))
        self.father_name.setText(c.get('father_name', ''))
        self.gender.setCurrentText(c.get('gender', 'Male'))
        self.cust_type.setCurrentText(c.get('customer_type', 'Individual'))
        self.nationality.setText(c.get('nationality', 'Pakistani'))
        
        self.phone.setText(c.get('phone_primary', ''))
        self.whatsapp.setText(c.get('phone_whatsapp', ''))
        self.email.setText(c.get('email', ''))
        self.address.setPlainText(c.get('address', ''))
        
        self.passport.setText(c.get('passport_number', ''))
        self.cnic.setText(c.get('cnic', ''))
        
        # Populate family members
        if 'family_members' in c:
            for fam in c['family_members']:
                self._add_fam_row()
                row = self.fam_table.rowCount() - 1
                self.fam_table.item(row, 0).setText(fam.get('full_name', ''))
                self.fam_table.item(row, 1).setText(fam.get('relation', ''))
                self.fam_table.item(row, 2).setText(str(fam.get('age', '')))
                
        # Populate emergency contacts
        if 'emergency_contacts' in c:
            for em in c['emergency_contacts']:
                self._add_emerg_row()
                row = self.emerg_table.rowCount() - 1
                self.emerg_table.item(row, 0).setText(em.get('contact_name', ''))
                self.emerg_table.item(row, 1).setText(em.get('relation', ''))
                self.emerg_table.item(row, 2).setText(em.get('phone', ''))
        
        # NOTE: ignoring DOB and expiry parsing for now to keep simple
        
    def get_data(self):
        return {
            'title': self.title_cb.currentText(),
            'first_name': self.first_name.text().strip(),
            'last_name': self.last_name.text().strip(),
            'father_name': self.father_name.text().strip(),
            'gender': self.gender.currentText(),
            'customer_type': self.cust_type.currentText(),
            'nationality': self.nationality.text().strip(),
            'phone_primary': self.phone.text().strip(),
            'phone_whatsapp': self.whatsapp.text().strip(),
            'email': self.email.text().strip(),
            'address': self.address.toPlainText().strip(),
            'passport_number': self.passport.text().strip(),
            'cnic': self.cnic.text().strip(),
            'is_vip': self.is_vip.isChecked(),
            'family_members': self._get_table_data(self.fam_table, ['full_name', 'relation', 'age']),
            'emergency_contacts': self._get_table_data(self.emerg_table, ['contact_name', 'relation', 'phone'])
        }
        
    def _get_table_data(self, table, keys):
        data = []
        for i in range(table.rowCount()):
            row_data = {}
            empty_row = True
            for j, key in enumerate(keys):
                item = table.item(i, j)
                val = item.text().strip() if item else ""
                row_data[key] = val
                if val:
                    empty_row = False
            if not empty_row:
                data.append(row_data)
        return data
        
    def _open_scanner(self):
        try:
            from PySide6.QtWidgets import QFileDialog, QMessageBox
            
            # Open file dialog
            file_name, _ = QFileDialog.getOpenFileName(
                self, "Upload Passport Image", "", "Image Files (*.jpg *.jpeg *.png)"
            )
            
            if file_name:
                from services.ocr_service import OcrService
                service = OcrService()
                
                # Extract data using the new PIL-based service
                extracted_data = service.extract_mrz_data(file_name)
                
                # Call success handler
                self._on_scan_success(extracted_data)
                QMessageBox.information(self, "Success", "Passport data extracted successfully!")
                
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Scanner Error",
                f"An error occurred while processing the passport:\n\n{e}")
        
    def _on_scan_success(self, data):
        # Auto-fill fields
        if data.get('first_name'):
            self.first_name.setText(data['first_name'])
            
        if data.get('last_name'):
            self.last_name.setText(data['last_name'])
            
        if data.get('passport_number'):
            self.passport.setText(data['passport_number'])
            
        if data.get('dob'):
            try:
                parts = data['dob'].split('-')
                self.dob.setDate(QDate(int(parts[0]), int(parts[1]), int(parts[2])))
            except:
                pass
                
        if data.get('expiry_date'):
            try:
                parts = data['expiry_date'].split('-')
                self.pass_expiry.setDate(QDate(int(parts[0]), int(parts[1]), int(parts[2])))
            except:
                pass
                
        if data.get('nationality'):
            self.nationality.setText(data['nationality'])
            
        if data.get('father_husband_name'):
            self.father_name.setText(data['father_husband_name'])
            
        if data.get('cnic'):
            self.cnic.setText(data['cnic'])
        
    def _save(self):
        if not self.first_name.text().strip() or not self.phone.text().strip():
            QMessageBox.warning(self, "Validation Error", "First Name and Primary Phone are required.")
            return
            
        self.accept()

    def clear_form(self):
        self.customer = None
        self.setWindowTitle("New Customer")
        self.title_cb.setCurrentIndex(0)
        self.first_name.clear()
        self.last_name.clear()
        self.father_name.clear()
        self.gender.setCurrentIndex(0)
        self.cust_type.setCurrentIndex(0)
        self.nationality.clear()
        self.phone.clear()
        self.whatsapp.clear()
        self.email.clear()
        self.address.clear()
        self.passport.clear()
        self.cnic.clear()
        self.is_vip.setChecked(False)
        self.fam_table.setRowCount(0)
        self.emerg_table.setRowCount(0)
        self.dob.setDate(QDate.currentDate())
        self.pass_expiry.setDate(QDate.currentDate())
        
    def load_customer(self, customer):
        self.customer = customer
        self.setWindowTitle(f"Edit Customer: {customer.get('first_name', '')}")
        self._populate_data()
