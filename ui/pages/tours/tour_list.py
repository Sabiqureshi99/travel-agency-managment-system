from core.permissions import has_permission, Modules, Actions
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QTabWidget, QTableWidget, 
                               QHeaderView, QMessageBox)

class TourListPage(QWidget):
    def __init__(self, current_user, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self._setup_ui()
        self._load_data()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        header = QHBoxLayout()
        title = QLabel("Tours Management")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.btn_add_pkg = QPushButton("Add Tour Package")
        self.btn_add_pkg.setObjectName("btn_primary")
        self.btn_add_pkg.setShortcut("Return")
        self.btn_add_pkg.clicked.connect(self._on_add_package_clicked)
        
        self.btn_add_bkg = QPushButton("Add Booking")
        self.btn_add_bkg.setObjectName("btn_secondary")
        self.btn_add_bkg.clicked.connect(self._on_add_booking_clicked)
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.btn_add_pkg)
        header.addWidget(self.btn_add_bkg)
        layout.addLayout(header)
        
        self.tabs = QTabWidget()
        
        # Packages Tab
        tab_pkg = QWidget()
        l_pkg = QVBoxLayout(tab_pkg)
        self.tbl_pkg = QTableWidget(0, 8)
        self.tbl_pkg.setHorizontalHeaderLabels([
            "Code", "Name", "Destination", "Days", "Nights", "Price", "Status", "Actions"
        ])
        self.tbl_pkg.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        l_pkg.addWidget(self.tbl_pkg)
        self.tabs.addTab(tab_pkg, "Packages")
        
        # Bookings Tab
        tab_bkg = QWidget()
        l_bkg = QVBoxLayout(tab_bkg)
        self.tbl_bkg = QTableWidget(0, 9)
        self.tbl_bkg.setHorizontalHeaderLabels([
            "Booking#", "Package", "Customer", "Pax", "Travel Date", "Total", "Paid", "Status", "Actions"
        ])
        self.tbl_bkg.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        l_bkg.addWidget(self.tbl_bkg)
        self.tabs.addTab(tab_bkg, "Bookings")
        
        layout.addWidget(self.tabs)
        
    def _load_data(self):
        pass
        
    def refresh(self):
        self._load_data()

    def _on_add_package_clicked(self):
        """Open form to add a new tour package (stub)."""
        QMessageBox.information(self, "Coming Soon", "Tour package creation will be implemented in a future update.")

    def _on_add_booking_clicked(self):
        """Open form to add a new tour booking (stub)."""
        QMessageBox.information(self, "Coming Soon", "Tour booking creation will be implemented in a future update.")
