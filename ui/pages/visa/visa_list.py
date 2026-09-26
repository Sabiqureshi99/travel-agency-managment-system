from core.permissions import has_permission, Modules, Actions
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QLineEdit, QComboBox, QTableWidget, 
                               QHeaderView, QTableWidgetItem, QMessageBox, QAbstractItemView)
from PySide6.QtCore import Qt
from utils.formatters import format_currency

class VisaListPage(QWidget):
    def __init__(self, current_user, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self._setup_ui()
        self._load_data()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        header = QHBoxLayout()
        title = QLabel("Visa Applications")
        title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 16px;")
        self.btn_add = QPushButton("+ Add Application")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.btn_add)
        layout.addLayout(header)
        
        filters = QHBoxLayout()
        filters.setContentsMargins(16, 0, 16, 16)
        self.status_cb = QComboBox()
        self.status_cb.addItems(["All", "Pending", "In Process", "Approved", "Rejected"])
        self.country_cb = QComboBox()
        self.country_cb.addItems(["All", "UAE", "Saudi Arabia", "Turkey", "UK", "USA", "Schengen"])
        self.search_input = QLineEdit(placeholderText="Search App#, Customer...")
        
        filters.addWidget(QLabel("Status:"))
        filters.addWidget(self.status_cb)
        filters.addWidget(QLabel("Country:"))
        filters.addWidget(self.country_cb)
        filters.addWidget(self.search_input)
        
        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self.refresh)
        filters.addWidget(self.btn_refresh)
        layout.addLayout(filters)
        
        table_container = QVBoxLayout()
        table_container.setContentsMargins(16, 0, 16, 16)
        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels([
            "App#", "Customer", "Country", "Type", "Applied", "Appointment", "Status", "Total Cost", "Actions"
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(45)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.doubleClicked.connect(self._on_row_double_click)
        table_container.addWidget(self.table)
        layout.addLayout(table_container)
        
        pagination = QHBoxLayout()
        pagination.addStretch()
        pagination.addWidget(QPushButton("< Prev"))
        pagination.addWidget(QLabel("Page 1"))
        pagination.addWidget(QPushButton("Next >"))
        pagination.addStretch()
        layout.addLayout(pagination)
        
        self.btn_add.setEnabled(has_permission(self.current_user, Modules.VISA, Actions.ADD))
        self.btn_add.clicked.connect(self._on_add_application)
        
    def _load_data(self):
        from viewmodels.visa_viewmodel import VisaViewModel
        if not hasattr(self, 'viewmodel'):
            self.viewmodel = VisaViewModel()
            self.viewmodel.visas_loaded.connect(self._on_visas_loaded)
            self.viewmodel.visa_saved.connect(self.refresh)
            self.viewmodel.error_occurred.connect(self._on_error)
            
        search_query = self.search_input.text()
        self.viewmodel.load_visas(query=search_query, skip=0, limit=100)
        
    def refresh(self):
        self._load_data()

    def _on_visas_loaded(self, result):
        visas = result.get('items', [])
        self.table.setRowCount(0)
        self._visas = visas
        for i, v in enumerate(visas):
            self.table.insertRow(i)
            
            self.table.setItem(i, 0, QTableWidgetItem(getattr(v, 'application_number', '')))
            
            customer_name = v.customer.full_name if getattr(v, 'customer', None) else ""
            self.table.setItem(i, 1, QTableWidgetItem(customer_name))
            
            self.table.setItem(i, 2, QTableWidgetItem(getattr(v, 'country', '')))
            self.table.setItem(i, 3, QTableWidgetItem(getattr(v, 'visa_type', '')))
            self.table.setItem(i, 4, QTableWidgetItem(str(getattr(v, 'application_date', ''))))
            self.table.setItem(i, 5, QTableWidgetItem(str(getattr(v, 'appointment_date', ''))))
            
            status = getattr(v, 'status', '')
            status_item = QTableWidgetItem(status)
            if status == "Approved":
                status_item.setForeground(Qt.GlobalColor.green)
            elif status == "Rejected":
                status_item.setForeground(Qt.GlobalColor.red)
            else:
                status_item.setForeground(Qt.GlobalColor.darkYellow)
            self.table.setItem(i, 6, status_item)
            
            total = getattr(v, 'total_cost', 0)
            self.table.setItem(i, 7, QTableWidgetItem(format_currency(total)))
            
            edit_btn = QPushButton("Edit")
            edit_btn.setObjectName("btn_secondary")
            edit_btn.setEnabled(has_permission(self.current_user, Modules.VISA, Actions.EDIT))
            edit_btn.clicked.connect(lambda checked, idx=i: self._on_row_double_click(idx))
            self.table.setCellWidget(i, 8, edit_btn)

    def _on_error(self, message):
        QMessageBox.warning(self, "Error", message)

    def _on_add_application(self):
        from ui.pages.visa.visa_form import VisaForm
        dialog = VisaForm(self.viewmodel, self.current_user.id, parent=self)
        if dialog.exec():
            self.refresh()
                
    def _on_row_double_click(self, index):
        if not has_permission(self.current_user, Modules.VISA, Actions.EDIT): return
        if not hasattr(self, '_visas'):
            return
        row = index if isinstance(index, int) else index.row()
        v = self._visas[row]
        
        from ui.pages.visa.visa_form import VisaForm
        dialog = VisaForm(self.viewmodel, self.current_user.id, application=v, parent=self)
        if dialog.exec():
            self.refresh()
