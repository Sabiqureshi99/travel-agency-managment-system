from core.permissions import has_permission, Modules, Actions
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QLineEdit, QComboBox, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QAbstractItemView, QAbstractItemView)
from PySide6.QtCore import Qt
# Try to import services when available
try:
    from services.customer_service import CustomerService
except ImportError:
    CustomerService = None

class CustomerListPage(QWidget):
    def __init__(self, current_user, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self._setup_ui()
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, self._load_data)
        
        # Instantiate dialog once to avoid freezing the UI on button clicks
        from ui.pages.customers.customer_form import CustomerForm
        self.customer_form_dialog = CustomerForm(parent=self)
        
        # Pagination state
        self.current_page = 1
        self.page_size = 50
        self.total_records = 0
        
        # Connect global signals for background refresh
        from core.signals import app_signals
        app_signals.umrah_checkout_completed.connect(self.refresh)
        app_signals.customer_added.connect(self.refresh)
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        header_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        title_label = QLabel("Customer Management")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        self.btn_add = QPushButton("Add Customer")
        self.btn_export = QPushButton("Export")
        self.btn_print = QPushButton("Print")
        
        # Permission check
        # if 'add_customer' not in self.current_user.permissions:
        #     self.btn_add.hide()
            
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_add)
        header_layout.addWidget(self.btn_export)
        header_layout.addWidget(self.btn_print)
        layout.addLayout(header_layout)
        
        # Search & Filter bar
        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search name, phone, CNIC, passport...")
        self.search_input.textChanged.connect(self.on_search)
        
        self.type_filter = QComboBox()
        self.type_filter.addItems(["All", "Individual", "Corporate", "VIP"])
        self.type_filter.currentTextChanged.connect(self.on_search)
        
        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self.refresh)
        
        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(self.type_filter)
        filter_layout.addWidget(self.btn_refresh)
        layout.addLayout(filter_layout)
        
        # Data Table
        self.table = QTableWidget(0, 9)
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
            "Code", "Name", "Phone", "CNIC", "Passport", "Expiry", "City", "Type", "Actions"
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(60)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(8, 180)
        self.table.doubleClicked.connect(self._on_row_double_click)
        layout.addWidget(self.table)
        
        # Pagination
        pagination_layout = QHBoxLayout()
        pagination_layout.addStretch()
        self.btn_prev = QPushButton("< Prev")
        self.lbl_page = QLabel("Page 1 of 1")
        self.btn_next = QPushButton("Next >")
        pagination_layout.addWidget(self.btn_prev)
        pagination_layout.addWidget(self.lbl_page)
        pagination_layout.addWidget(self.btn_next)
        pagination_layout.addStretch()
        layout.addLayout(pagination_layout)
        
        # Connect signals
        self.btn_export.clicked.connect(self._export_data)
        self.btn_add.setEnabled(has_permission(self.current_user, Modules.CUSTOMERS, Actions.ADD))
        self.btn_add.clicked.connect(self._on_add_customer)
        
        self.btn_prev.clicked.connect(self._prev_page)
        self.btn_next.clicked.connect(self._next_page)
        
    def _load_data(self):
        from viewmodels.customer_viewmodel import CustomerViewModel
        if not hasattr(self, 'viewmodel'):
            self.viewmodel = CustomerViewModel()
            self.viewmodel.customers_loaded.connect(self._on_customers_loaded)
            self.viewmodel.customer_saved.connect(self.refresh)
            self.viewmodel.customer_deleted.connect(self.refresh)
            self.viewmodel.error_occurred.connect(self._on_error)
            
        search_query = self.search_input.text()
        skip = (self.current_page - 1) * self.page_size
        self.viewmodel.load_customers(query=search_query, skip=skip, limit=self.page_size)
            
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
        
    def _on_customers_loaded(self, customers, total):
        self.total_records = total
        import math
        total_pages = max(1, math.ceil(self.total_records / self.page_size))
        self.lbl_page.setText(f"Page {self.current_page} of {total_pages}")
        self.btn_prev.setEnabled(self.current_page > 1)
        self.btn_next.setEnabled(self.current_page < total_pages)
        
        self.table.setRowCount(0)
        self._customers = customers  # Store local reference
        for i, cust in enumerate(self._customers):
            self.table.insertRow(i)
            self.table.setRowHeight(i, 60) # Explicitly set row height
            
            # "Code", "Name", "Phone", "CNIC", "Passport", "Expiry", "City", "Type", "Actions"
            self.table.setItem(i, 0, QTableWidgetItem(getattr(cust, 'customer_code', '')))
            self.table.setItem(i, 1, QTableWidgetItem(getattr(cust, 'full_name', '')))
            self.table.setItem(i, 2, QTableWidgetItem(getattr(cust, 'phone_primary', '')))
            self.table.setItem(i, 3, QTableWidgetItem(getattr(cust, 'cnic', '')))
            self.table.setItem(i, 4, QTableWidgetItem(getattr(cust, 'passport_number', '')))
            expiry = getattr(cust, 'passport_expiry_date', '')
            self.table.setItem(i, 5, QTableWidgetItem(str(expiry) if expiry else ''))
            self.table.setItem(i, 6, QTableWidgetItem(getattr(cust, 'city', '')))
            self.table.setItem(i, 7, QTableWidgetItem(getattr(cust, 'customer_type', '')))
            
            # Action button
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 4, 4, 4)
            action_layout.setSpacing(8)
            action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            edit_btn = QPushButton("Edit")
            edit_btn.setObjectName("btn_secondary")
            edit_btn.setMinimumWidth(70)
            edit_btn.setEnabled(has_permission(self.current_user, Modules.CUSTOMERS, Actions.EDIT))
            edit_btn.clicked.connect(lambda checked, idx=i: self._on_row_double_click(idx))
            
            del_btn = QPushButton("Delete")
            del_btn.setStyleSheet("background-color: #ef4444; color: white; border: none; border-radius: 4px; padding: 6px 12px; font-weight: bold;")
            del_btn.setMinimumWidth(70)
            del_btn.setEnabled(has_permission(self.current_user, Modules.CUSTOMERS, Actions.DELETE))
            del_btn.clicked.connect(lambda checked, idx=i: self._on_delete_customer(idx))
            
            action_layout.addWidget(edit_btn)
            action_layout.addWidget(del_btn)
            action_layout.addStretch()
            
            self.table.setCellWidget(i, 8, action_widget)
            
    def _on_error(self, message):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.warning(self, "Error", message)
        
    def _on_delete_customer(self, row):
        if not has_permission(self.current_user, Modules.CUSTOMERS, Actions.DELETE): return
        if not hasattr(self, '_customers'):
            return
        cust = self._customers[row]
        
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, 'Delete Customer', 
                                     f"Are you sure you want to delete {cust.first_name} {cust.last_name}?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.viewmodel.delete_customer(cust.id, self.current_user.id)
            
    def _on_add_customer(self):
        if not has_permission(self.current_user, Modules.CUSTOMERS, Actions.ADD): return
        from PySide6.QtWidgets import QDialog
        self.customer_form_dialog.clear_form()
        if self.customer_form_dialog.exec() == QDialog.DialogCode.Accepted:
            customer_data = self.customer_form_dialog.get_data()
            if customer_data:
                self.viewmodel.save_customer(customer_data, self.current_user.id)
                
    def _on_row_double_click(self, index):
        if not has_permission(self.current_user, Modules.CUSTOMERS, Actions.EDIT): return
        if not hasattr(self, '_customers'):
            return
        # If index is an int (from button), or a QModelIndex (from double click)
        row = index if isinstance(index, int) else index.row()
        cust = self._customers[row]
        
        from ui.pages.customers.customer_form import CustomerForm
        from PySide6.QtWidgets import QDialog
        
        from config.database import get_session
        from models.customer import Customer
        
        with get_session() as session:
            fresh_cust = session.get(Customer, cust.id)
            if not fresh_cust:
                return
                
            cust_dict = {
                'id': getattr(fresh_cust, 'id', ''),
                'title': getattr(fresh_cust, 'title', ''),
                'first_name': getattr(fresh_cust, 'first_name', ''),
                'last_name': getattr(fresh_cust, 'last_name', ''),
                'father_name': getattr(fresh_cust, 'father_name', ''),
                'gender': getattr(fresh_cust, 'gender', ''),
                'customer_type': getattr(fresh_cust, 'customer_type', ''),
                'nationality': getattr(fresh_cust, 'nationality', ''),
                'phone_primary': getattr(fresh_cust, 'phone_primary', ''),
                'phone_whatsapp': getattr(fresh_cust, 'phone_whatsapp', ''),
                'email': getattr(fresh_cust, 'email', ''),
                'address': getattr(fresh_cust, 'address', ''),
                'passport_number': getattr(fresh_cust, 'passport_number', ''),
                'cnic': getattr(fresh_cust, 'cnic', ''),
                'city': getattr(fresh_cust, 'city', ''),
                'is_vip': getattr(fresh_cust, 'is_vip', False),
                'family_members': [
                    {'full_name': f.full_name, 'relation': getattr(f, 'relation', ''), 'age': getattr(f, 'age', '')}
                    for f in getattr(fresh_cust, 'family_members', [])
                ],
                'emergency_contacts': [
                    {'contact_name': e.contact_name, 'relation': getattr(e, 'relation', ''), 'phone': getattr(e, 'phone', '')}
                    for e in getattr(fresh_cust, 'emergency_contacts', [])
                ]
            }
        
        from PySide6.QtWidgets import QDialog
        self.customer_form_dialog.load_customer(cust_dict)
        if self.customer_form_dialog.exec() == QDialog.DialogCode.Accepted:
            customer_data = self.customer_form_dialog.get_data()
            if customer_data:
                customer_data['id'] = cust.id
                self.viewmodel.save_customer(customer_data, self.current_user.id)
        
    def _export_data(self):
        if CustomerService:
            try:
                CustomerService().export_customers_to_excel()
            except Exception as e:
                pass
