from core.permissions import has_permission, Modules, Actions
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
                               QHeaderView, QMessageBox, QAbstractItemView)
from viewmodels.visa_viewmodel import VisaViewModel

class VisaListPage(QWidget):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self._visas = []
        
        self.current_page = 1
        self.page_size = 50
        self.total_records = 0
        
        self.init_ui()
        self._load_data()
        
        # Connect global signals for background refresh
        from core.signals import app_signals
        app_signals.umrah_checkout_completed.connect(self.refresh)
        app_signals.visa_added.connect(self.refresh)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Header
        header_layout = QHBoxLayout()
        header_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        title = QLabel("Visa Applications")
        title.setObjectName("page_title")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        self.btn_add = QPushButton("+ New Application")
        self.btn_add.setFixedWidth(150)
        self.btn_add.setObjectName("btn_primary")
        self.btn_add.setShortcut("Return")
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_add)
        layout.addLayout(header_layout)

        # Toolbar
        toolbar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by Application #, Country...")
        self.search_input.setFixedWidth(300)
        self.search_input.textChanged.connect(self.on_search)
        
        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self.refresh)
        
        toolbar.addWidget(self.search_input)
        toolbar.addWidget(self.btn_refresh)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Table
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "App #", "Country", "Type", "App Date", "Total Cost", "Status", "Actions"
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(45)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.doubleClicked.connect(self._on_row_double_click)
        layout.addWidget(self.table)
        
        pagination_layout = QHBoxLayout()
        pagination_layout.addStretch()
        self.btn_prev = QPushButton("< Prev")
        self.lbl_page = QLabel("Page 1 of 1")
        self.btn_next = QPushButton("Next >")
        self.btn_prev.clicked.connect(self._prev_page)
        self.btn_next.clicked.connect(self._next_page)
        pagination_layout.addWidget(self.btn_prev)
        pagination_layout.addWidget(self.lbl_page)
        pagination_layout.addWidget(self.btn_next)
        pagination_layout.addStretch()
        layout.addLayout(pagination_layout)

        self.btn_add.setEnabled(has_permission(self.current_user, Modules.VISA, Actions.ADD))
        self.btn_add.clicked.connect(self._on_add_visa)

    def _load_data(self):
        if not hasattr(self, 'viewmodel'):
            self.viewmodel = VisaViewModel()
            self.viewmodel.visas_loaded.connect(self._on_visas_loaded)
            self.viewmodel.error_occurred.connect(self._on_error)
            
        search_query = self.search_input.text()
        skip = (self.current_page - 1) * self.page_size
        self.viewmodel.load_visas(query=search_query, skip=skip, limit=self.page_size)

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

    def _on_visas_loaded(self, result):
        self.total_records = result.get('total', 0)
        import math
        total_pages = max(1, math.ceil(self.total_records / self.page_size))
        self.lbl_page.setText(f"Page {self.current_page} of {total_pages}")
        self.btn_prev.setEnabled(self.current_page > 1)
        self.btn_next.setEnabled(self.current_page < total_pages)
        
        self.table.setRowCount(0)
        self._visas = result.get('items', [])
        
        for i, visa in enumerate(self._visas):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(getattr(visa, 'application_number', '')))
            self.table.setItem(i, 1, QTableWidgetItem(getattr(visa, 'country', '')))
            self.table.setItem(i, 2, QTableWidgetItem(getattr(visa, 'visa_type', '')))
            date_str = str(getattr(visa, 'application_date', ''))
            self.table.setItem(i, 3, QTableWidgetItem(date_str))
            self.table.setItem(i, 4, QTableWidgetItem(str(getattr(visa, 'total_cost', 0))))
            self.table.setItem(i, 5, QTableWidgetItem(getattr(visa, 'status', '')))
            
            # Action button
            edit_btn = QPushButton("Edit")
            edit_btn.setObjectName("btn_secondary")
            edit_btn.setEnabled(has_permission(self.current_user, Modules.VISA, Actions.EDIT))
            edit_btn.clicked.connect(lambda checked, idx=i: self._on_row_double_click(idx))
            self.table.setCellWidget(i, 6, edit_btn)

    def _on_add_visa(self):
        from ui.pages.visas.visa_form import VisaFormDialog
        dialog = VisaFormDialog(parent=self, current_user_id=self.current_user.id)
        if dialog.exec():
            self.refresh()

    def _on_row_double_click(self, row):
        if not has_permission(self.current_user, Modules.VISA, Actions.EDIT): return
        if 0 <= row < len(self._visas):
            visa = self._visas[row]
            from ui.pages.visas.visa_form import VisaFormDialog
            dialog = VisaFormDialog(parent=self, visa=visa, current_user_id=self.current_user.id)
            if dialog.exec():
                self.refresh()

    def _on_error(self, message):
        QMessageBox.critical(self, "Error", message)
