from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QLineEdit, QComboBox, QTabWidget, 
                               QWidget, QDateEdit, QCheckBox, QMessageBox, QGridLayout)
from PySide6.QtCore import QDate

class EmployeeForm(QDialog):
    def __init__(self, employee=None, parent=None):
        super().__init__(parent)
        self.employee = employee
        self.setWindowTitle("Employee Form")
        self.setMinimumSize(600, 400)
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        
        # Tab 1: Personal
        tab_personal = QWidget()
        t1_layout = QVBoxLayout(tab_personal)
        self.name_edit = QLineEdit(placeholderText="Full Name *")
        self.phone_edit = QLineEdit(placeholderText="Phone *")
        self.cnic_edit = QLineEdit(placeholderText="CNIC")
        self.dob_edit = QDateEdit()
        self.dob_edit.setCalendarPopup(True)
        t1_layout.addWidget(self.name_edit)
        t1_layout.addWidget(self.phone_edit)
        t1_layout.addWidget(self.cnic_edit)
        t1_layout.addWidget(QLabel("Date of Birth:"))
        t1_layout.addWidget(self.dob_edit)
        self.tabs.addTab(tab_personal, "Personal Info")
        
        # Tab 2: Job
        tab_job = QWidget()
        t2_layout = QVBoxLayout(tab_job)
        self.dept_cb = QComboBox()
        self.dept_cb.addItems(["Sales", "Ticketing", "Visa", "Accounts", "HR"])
        self.desig_edit = QLineEdit(placeholderText="Designation")
        self.date_joined = QDateEdit(QDate.currentDate())
        self.date_joined.setCalendarPopup(True)
        self.status_cb = QComboBox()
        self.status_cb.addItems(["Active", "Inactive"])
        t2_layout.addWidget(QLabel("Department:"))
        t2_layout.addWidget(self.dept_cb)
        t2_layout.addWidget(self.desig_edit)
        t2_layout.addWidget(QLabel("Date Joined:"))
        t2_layout.addWidget(self.date_joined)
        t2_layout.addWidget(QLabel("Status:"))
        t2_layout.addWidget(self.status_cb)
        self.tabs.addTab(tab_job, "Job Info")
        
        # Tab 3: Salary
        tab_salary = QWidget()
        t3_layout = QVBoxLayout(tab_salary)
        self.salary_base = QLineEdit(placeholderText="Base Salary")
        self.bank_name = QLineEdit(placeholderText="Bank Name")
        self.account_num = QLineEdit(placeholderText="Account Number")
        t3_layout.addWidget(self.salary_base)
        t3_layout.addWidget(self.bank_name)
        t3_layout.addWidget(self.account_num)
        self.tabs.addTab(tab_salary, "Salary")
        
        # Tab 4: Login Account
        tab_login = QWidget()
        t4_layout = QVBoxLayout(tab_login)
        self.create_login = QCheckBox("Create System Login")
        self.username = QLineEdit(placeholderText="Username")
        self.password = QLineEdit(placeholderText="Password")
        self.password.setEchoMode(QLineEdit.Password)
        t4_layout.addWidget(self.create_login)
        t4_layout.addWidget(self.username)
        t4_layout.addWidget(self.password)
        self.tabs.addTab(tab_login, "Login Account")
        
        # Tab 5: Permissions
        tab_perms = QWidget()
        t5_layout = QGridLayout(tab_perms)
        modules = [
            ("dashboard", "Dashboard"),
            ("customers", "Customers"),
            ("flights", "Flights"),
            ("visa", "Visa"),
            ("umrah", "Umrah"),
            ("hotels", "Hotels"),
            ("transport", "Transport"),
            ("accounting", "Accounting"),
            ("reports", "Reports")
        ]
        
        self.perm_checkboxes = {}
        for row, (mod_id, mod_name) in enumerate(modules):
            t5_layout.addWidget(QLabel(mod_name), row, 0)
            cb_view = QCheckBox("View")
            cb_add = QCheckBox("Add")
            cb_edit = QCheckBox("Edit")
            cb_delete = QCheckBox("Delete")
            t5_layout.addWidget(cb_view, row, 1)
            t5_layout.addWidget(cb_add, row, 2)
            t5_layout.addWidget(cb_edit, row, 3)
            t5_layout.addWidget(cb_delete, row, 4)
            self.perm_checkboxes[mod_id] = {
                "view": cb_view,
                "add": cb_add,
                "edit": cb_edit,
                "delete": cb_delete
            }
        
        self.tabs.addTab(tab_perms, "Permissions")
        
        layout.addWidget(self.tabs)
        
        # Footer
        footer = QHBoxLayout()
        self.btn_cancel = QPushButton("Cancel")
        self.btn_save = QPushButton("Save")
        self.btn_save.setShortcut("Return")
        footer.addStretch()
        footer.addWidget(self.btn_cancel)
        footer.addWidget(self.btn_save)
        layout.addLayout(footer)
        
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self._save)
        
        if self.employee:
            self._populate_data()
            
    def _populate_data(self):
        e = self.employee
        
        # We need a first/last name split since form has only one name_edit
        first = e.get('first_name', '')
        last = e.get('last_name', '')
        self.name_edit.setText(f"{first} {last}".strip())
        self.phone_edit.setText(e.get('phone', ''))
        self.cnic_edit.setText(e.get('cnic', ''))
        self.dept_cb.setCurrentText(e.get('department', 'Sales'))
        self.desig_edit.setText(e.get('designation', ''))
        # Note: skipping dates for now to keep simple
        self.salary_base.setText(str(e.get('base_salary', '')))
        self.bank_name.setText(e.get('bank_name', ''))
        self.account_num.setText(e.get('bank_account_number', ''))
        
        login_data = e.get('login_data')
        if login_data:
            self.create_login.setChecked(True)
            self.username.setText(login_data.get('username', ''))
            
            permissions = login_data.get('permissions', {})
            for mod_id, cbs in self.perm_checkboxes.items():
                mod_perms = permissions.get(mod_id, [])
                if "view" in mod_perms: cbs["view"].setChecked(True)
                if "add" in mod_perms: cbs["add"].setChecked(True)
                if "edit" in mod_perms: cbs["edit"].setChecked(True)
                if "delete" in mod_perms: cbs["delete"].setChecked(True)
        
    def get_data(self):
        full_name = self.name_edit.text().strip()
        parts = full_name.split(' ', 1)
        first_name = parts[0] if parts else ""
        last_name = parts[1] if len(parts) > 1 else ""
        
        permissions = {}
        for mod_id, cbs in self.perm_checkboxes.items():
            actions = []
            if cbs["view"].isChecked(): actions.append("view")
            if cbs["add"].isChecked(): actions.append("add")
            if cbs["edit"].isChecked(): actions.append("edit")
            if cbs["delete"].isChecked(): actions.append("delete")
            if actions:
                permissions[mod_id] = actions
                
        login_data = None
        if self.create_login.isChecked() and self.username.text().strip():
            login_data = {
                "username": self.username.text().strip(),
                "password": self.password.text().strip(),
                "permissions": permissions
            }
        
        return {
            'first_name': first_name,
            'last_name': last_name,
            'phone': self.phone_edit.text().strip(),
            'cnic': self.cnic_edit.text().strip(),
            'department': self.dept_cb.currentText(),
            'designation': self.desig_edit.text().strip(),
            'base_salary': float(self.salary_base.text() or 0),
            'bank_name': self.bank_name.text().strip(),
            'bank_account_number': self.account_num.text().strip(),
            'date_joined': self.date_joined.date().toPython(),
            'login_data': login_data
        }
        
    def _save(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Name is required")
            return
        if not self.phone_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Phone number is required")
            return
        self.accept()
