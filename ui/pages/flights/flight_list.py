from core.permissions import has_permission, Modules, Actions
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
                               QHeaderView, QComboBox, QMessageBox, QAbstractItemView)
from PySide6.QtCore import Qt
from viewmodels.flight_viewmodel import FlightViewModel

class FlightListPage(QWidget):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self._flights = []
        
        self.current_page = 1
        self.page_size = 50
        self.total_records = 0
        
        self.init_ui()
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, self._load_data)
        
        # Connect global signals for background refresh
        from core.signals import app_signals
        app_signals.umrah_checkout_completed.connect(self.refresh)
        app_signals.flight_added.connect(self.refresh)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Header
        header_layout = QHBoxLayout()
        # Phase 1: Header Alignment Fix (Aligning title and button vertically)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        title = QLabel("Flight Bookings")
        title.setObjectName("page_title")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        self.btn_add = QPushButton("+ Book Flight")
        self.btn_add.setObjectName("btn_primary")
        self.btn_add.setShortcut("Return")
        self.btn_add.setFixedWidth(150)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_add)
        layout.addLayout(header_layout)

        # Toolbar
        toolbar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by PNR, Airline, City...")
        self.search_input.setFixedWidth(300)
        self.search_input.textChanged.connect(self.on_search)
        
        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self.refresh)
        
        toolbar.addWidget(self.search_input)
        toolbar.addWidget(self.btn_refresh)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Table
        self.table = QTableWidget(0, 11)
        self.table.setHorizontalHeaderLabels([
            "Booking #", "PNR", "Airline", "Flight No", "Origin", 
            "Destination", "Dep Time", "Arr Time", "Date", "Status", "Actions"
        ])
        
        # Phase 1: Table Header Fix (Hide vertical header to remove the ugly white block glitch)
        self.table.verticalHeader().setVisible(False)
        # Phase 1: Table Row Fix (Increase row height to 45 so buttons fit nicely)
        self.table.verticalHeader().setDefaultSectionSize(45)
        
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.doubleClicked.connect(lambda idx: self._on_edit(idx.row()))
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

        self.btn_add.setEnabled(has_permission(self.current_user, Modules.FLIGHTS, Actions.ADD))
        self.btn_add.clicked.connect(self._on_add)

    def _load_data(self):
        if not hasattr(self, 'viewmodel'):
            self.viewmodel = FlightViewModel()
            self.viewmodel.flights_loaded.connect(self._on_flights_loaded)
            self.viewmodel.error_occurred.connect(self._on_error)
            
        search_query = self.search_input.text()
        skip = (self.current_page - 1) * self.page_size
        self.viewmodel.load_flights(query=search_query, skip=skip, limit=self.page_size)

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

    def _on_flights_loaded(self, result):
        self.total_records = result.get('total', 0)
        import math
        total_pages = max(1, math.ceil(self.total_records / self.page_size))
        self.lbl_page.setText(f"Page {self.current_page} of {total_pages}")
        self.btn_prev.setEnabled(self.current_page > 1)
        self.btn_next.setEnabled(self.current_page < total_pages)
        
        self.table.setRowCount(0)
        self._flights = result.get('items', [])
        
        for i, flight in enumerate(self._flights):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(getattr(flight, 'booking_number', '')))
            self.table.setItem(i, 1, QTableWidgetItem(getattr(flight, 'pnr', '')))
            self.table.setItem(i, 2, QTableWidgetItem(getattr(flight, 'airline', '')))
            self.table.setItem(i, 3, QTableWidgetItem(getattr(flight, 'flight_number', '')))
            self.table.setItem(i, 4, QTableWidgetItem(getattr(flight, 'origin', '')))
            self.table.setItem(i, 5, QTableWidgetItem(getattr(flight, 'destination', '')))
            self.table.setItem(i, 6, QTableWidgetItem(getattr(flight, 'departure_time', '')))
            self.table.setItem(i, 7, QTableWidgetItem(getattr(flight, 'arrival_time', '')))
            date_str = str(getattr(flight, 'departure_date', ''))
            self.table.setItem(i, 8, QTableWidgetItem(date_str))
            self.table.setItem(i, 9, QTableWidgetItem(getattr(flight, 'booking_status', '')))
            
            # Action button
            edit_btn = QPushButton("Edit")
            edit_btn.setObjectName("btn_secondary")
            edit_btn.setEnabled(has_permission(self.current_user, Modules.FLIGHTS, Actions.EDIT))
            edit_btn.clicked.connect(lambda checked, idx=i: self._on_edit(idx))
            self.table.setCellWidget(i, 10, edit_btn)

    def _on_add(self):
        if not has_permission(self.current_user, Modules.FLIGHTS, Actions.ADD): return
        from ui.pages.flights.flight_form import FlightFormDialog
        dialog = FlightFormDialog(parent=self, current_user_id=self.current_user.id)
        if dialog.exec():
            self.refresh()

    def _on_edit(self, index):
        if not has_permission(self.current_user, Modules.FLIGHTS, Actions.EDIT): return
        flight = self._flights[index]
        from ui.pages.flights.flight_form import FlightFormDialog
        dialog = FlightFormDialog(parent=self, flight=flight, current_user_id=self.current_user.id)
        if dialog.exec():
            self.refresh()

    def _on_error(self, message):
        QMessageBox.critical(self, "Error", message)
