from core.permissions import has_permission, Modules, Actions
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QTableWidget, QTableWidgetItem, QLabel, QLineEdit, QMessageBox, QHeaderView)
from PySide6.QtCore import Qt
from viewmodels.hajj_viewmodel import HajjViewModel
from ui.pages.hajj.hajj_form import HajjGroupForm

class HajjListPage(QWidget):
    def __init__(self, current_user, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.viewmodel = HajjViewModel()
        
        self.viewmodel.groups_loaded.connect(self._on_groups_loaded)
        self.viewmodel.error_occurred.connect(self._on_error)
        
        self.current_skip = 0
        self.limit = 50
        
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        header_layout = QHBoxLayout()
        header_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        title = QLabel("Hajj Management")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.textChanged.connect(self.refresh)
        add_btn = QPushButton("Add Group")
        add_btn.clicked.connect(self._add_group)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.search_bar)
        header_layout.addWidget(add_btn)
        layout.addLayout(header_layout)
        
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(["Group Code", "Name", "Year", "Quota", "Filled", "Price", "Status", "Actions"])
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(45)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        from ui.components.pagination import PaginationWidget
        self.pagination = PaginationWidget()
        self.pagination.page_changed.connect(self._on_page_changed)
        layout.addWidget(self.pagination)

    def _on_page_changed(self, skip):
        self.current_skip = skip
        self.refresh(reset_page=False)

    def refresh(self, reset_page=True):
        if reset_page:
            self.current_skip = 0
        self.viewmodel.load_groups(self.search_bar.text(), skip=self.current_skip, limit=self.limit)

    def _on_groups_loaded(self, result):
        self.table.setRowCount(0)
        items = result.get('items', [])
        total = result.get('total', 0)
        self.pagination.update_pagination(total, self.current_skip, self.limit)
        
        for row, grp in enumerate(items):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(grp.group_code))
            self.table.setItem(row, 1, QTableWidgetItem(grp.group_name))
            self.table.setItem(row, 2, QTableWidgetItem(str(grp.year)))
            self.table.setItem(row, 3, QTableWidgetItem(str(grp.total_quota)))
            self.table.setItem(row, 4, QTableWidgetItem("0"))  # Dummy filled count
            self.table.setItem(row, 5, QTableWidgetItem(str(grp.package_price)))
            self.table.setItem(row, 6, QTableWidgetItem(grp.status))
            self.table.setItem(row, 7, QTableWidgetItem("Edit"))

    def _add_group(self):
        dialog = HajjGroupForm(self.viewmodel, self.current_user.id, self)
        if dialog.exec():
            self.refresh()

    def _on_error(self, msg):
        QMessageBox.critical(self, "Error", msg)
