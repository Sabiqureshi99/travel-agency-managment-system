from core.permissions import has_permission, Modules, Actions
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QLineEdit, QComboBox, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QAbstractItemView, QAbstractItemView)

class EmployeeListPage(QWidget):
    def __init__(self, current_user, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        
        self.current_skip = 0
        self.limit = 50
        
        self._setup_ui()
        self._load_data()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        header_layout = QHBoxLayout()
        header_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        title = QLabel("Employee Management")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        self.btn_add = QPushButton("Add Employee")
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_add)
        layout.addLayout(header_layout)
        
        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search name, phone, CNIC...")
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "Active", "Inactive"])
        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(self.status_filter)
        layout.addLayout(filter_layout)
        
        self.table = QTableWidget(0, 8)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setStyleSheet("""
            QTableWidget {
                outline: none;
            }
            QTableWidget::item:selected {
                background-color: #2D142C;
                color: #FFFFFF;
                border-left: 3px solid #FF2E93;
            }
        """)
        self.table.setHorizontalHeaderLabels([
            "Code", "Name", "Phone", "Department", "Designation", "Date Joined", "Status", "Actions"
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(60)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(7, 180)
        layout.addWidget(self.table)
        
        from ui.components.pagination import PaginationWidget
        self.pagination = PaginationWidget()
        self.pagination.page_changed.connect(self._on_page_changed)
        layout.addWidget(self.pagination)
        
        self.table.doubleClicked.connect(self._on_row_double_click)
        self.btn_add.setEnabled(has_permission(self.current_user, Modules.EMPLOYEES, Actions.ADD))
        self.btn_add.clicked.connect(self._on_add_employee)
        
    def _load_data(self):
        from viewmodels.employee_viewmodel import EmployeeViewModel
        if not hasattr(self, 'viewmodel'):
            self.viewmodel = EmployeeViewModel()
            self.viewmodel.employees_loaded.connect(self._on_employees_loaded)
            self.viewmodel.employee_saved.connect(self.refresh)
            self.viewmodel.employee_deleted.connect(self.refresh)
            self.viewmodel.error_occurred.connect(self._on_error)
            
        search_query = self.search_input.text()
        self.viewmodel.load_employees(query=search_query, skip=self.current_skip, limit=self.limit)
        
    def _on_page_changed(self, skip):
        self.current_skip = skip
        self._load_data(reset_page=False)
        
    def refresh(self):
        self._load_data(reset_page=True)
        
    def _load_data(self, reset_page=True):
        if reset_page:
            self.current_skip = 0
            
        from viewmodels.employee_viewmodel import EmployeeViewModel
        if not hasattr(self, 'viewmodel'):
            self.viewmodel = EmployeeViewModel()
            self.viewmodel.employees_loaded.connect(self._on_employees_loaded)
            self.viewmodel.employee_saved.connect(self.refresh)
            self.viewmodel.employee_deleted.connect(self.refresh)
            self.viewmodel.error_occurred.connect(self._on_error)
            
        search_query = self.search_input.text()
        self.viewmodel.load_employees(query=search_query, skip=self.current_skip, limit=self.limit)
        
    def _on_employees_loaded(self, result):
        self.table.setRowCount(0)
        
        employees = result.get('items', [])
        total = result.get('total', 0)
        self.pagination.update_pagination(total, self.current_skip, self.limit)
        
        self._employees = employees
        for i, emp in enumerate(self._employees):
            self.table.insertRow(i)
            self.table.setRowHeight(i, 60)
            
            # "Code", "Name", "Phone", "Department", "Designation", "Date Joined", "Status", "Actions"
            self.table.setItem(i, 0, QTableWidgetItem(getattr(emp, 'employee_code', '')))
            self.table.setItem(i, 1, QTableWidgetItem(f"{getattr(emp, 'first_name', '')} {getattr(emp, 'last_name', '')}".strip()))
            self.table.setItem(i, 2, QTableWidgetItem(getattr(emp, 'phone', '')))
            self.table.setItem(i, 3, QTableWidgetItem(getattr(emp, 'department', '')))
            self.table.setItem(i, 4, QTableWidgetItem(getattr(emp, 'designation', '')))
            dj = getattr(emp, 'date_joined', '')
            self.table.setItem(i, 5, QTableWidgetItem(str(dj) if dj else ''))
            
            # Action button
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 4, 4, 4)
            action_layout.setSpacing(8)
            action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            edit_btn = QPushButton("Edit")
            edit_btn.setObjectName("btn_secondary")
            edit_btn.setMinimumWidth(70)
            edit_btn.setEnabled(has_permission(self.current_user, Modules.EMPLOYEES, Actions.EDIT))
            edit_btn.clicked.connect(lambda checked, idx=i: self._on_row_double_click(idx))
            
            del_btn = QPushButton("Delete")
            del_btn.setStyleSheet("background-color: #ef4444; color: white; border: none; border-radius: 4px; padding: 6px 12px; font-weight: bold;")
            del_btn.setMinimumWidth(70)
            del_btn.setEnabled(has_permission(self.current_user, Modules.EMPLOYEES, Actions.DELETE))
            del_btn.clicked.connect(lambda checked, idx=i: self._on_delete_employee(idx))
            
            action_layout.addWidget(edit_btn)
            action_layout.addWidget(del_btn)
            action_layout.addStretch()
            
            self.table.setCellWidget(i, 7, action_widget)
            
    def _on_error(self, message):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.warning(self, "Error", message)
        
    def _on_delete_employee(self, row):
        if not has_permission(self.current_user, Modules.EMPLOYEES, Actions.DELETE): return
        if not hasattr(self, '_employees'):
            return
        emp = self._employees[row]
        
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, 'Delete Employee', 
                                     f"Are you sure you want to delete {emp.first_name} {emp.last_name}?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.viewmodel.delete_employee(emp.id, self.current_user.id)
            
    def _on_add_employee(self):
        if not has_permission(self.current_user, Modules.EMPLOYEES, Actions.ADD): return
        from ui.pages.employees.employee_form import EmployeeForm
        from PySide6.QtWidgets import QDialog
        dialog = EmployeeForm(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            employee_data = dialog.get_data()
            if employee_data:
                self.viewmodel.save_employee(employee_data, self.current_user.id)
                
    def _on_row_double_click(self, index):
        if not has_permission(self.current_user, Modules.EMPLOYEES, Actions.EDIT): return
        if not hasattr(self, '_employees'):
            return
        row = index if isinstance(index, int) else index.row()
        emp = self._employees[row]
        
        from ui.pages.employees.employee_form import EmployeeForm
        from PySide6.QtWidgets import QDialog
        
        user = getattr(emp, 'user', None)
        login_data = None
        if user:
            login_data = {
                'username': getattr(user, 'username', ''),
                'permissions': getattr(user, 'permissions', {}) or {}
            }
            
        emp_dict = {
            'id': getattr(emp, 'id', ''),
            'first_name': getattr(emp, 'first_name', ''),
            'last_name': getattr(emp, 'last_name', ''),
            'phone': getattr(emp, 'phone', ''),
            'department': getattr(emp, 'department', ''),
            'designation': getattr(emp, 'designation', ''),
            'email': getattr(emp, 'email', ''),
            'cnic': getattr(emp, 'cnic', ''),
            'city': getattr(emp, 'city', ''),
            'address': getattr(emp, 'address', ''),
            'base_salary': getattr(emp, 'base_salary', 0),
            'bank_name': getattr(emp, 'bank_name', ''),
            'bank_account_number': getattr(emp, 'bank_account_number', ''),
            'login_data': login_data
        }
        
        dialog = EmployeeForm(employee=emp_dict, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            employee_data = dialog.get_data()
            if employee_data:
                employee_data['id'] = emp.id
                self.viewmodel.save_employee(employee_data, self.current_user.id)


