from core.permissions import has_permission, Modules, Actions
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QTableWidget, QTableWidgetItem, QTabWidget, QMessageBox, 
                               QHeaderView, QLabel, QLineEdit, QAbstractItemView)
from PySide6.QtCore import Qt
from viewmodels.hotel_viewmodel import HotelViewModel
from ui.pages.hotels.hotel_form import HotelForm, HotelBookingForm
from utils.formatters import format_currency

class HotelListPage(QWidget):
    def __init__(self, current_user, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.viewmodel = HotelViewModel()
        
        self.hotel_page = 1
        self.booking_page = 1
        self.page_size = 50
        self.total_hotels = 0
        self.total_bookings = 0
        
        self.viewmodel.hotels_loaded.connect(self._on_hotels_loaded)
        self.viewmodel.hotel_bookings_loaded.connect(self._on_bookings_loaded)
        self.viewmodel.error_occurred.connect(self._on_error)
        
        # Connect global signals for background refresh
        from core.signals import app_signals
        app_signals.umrah_checkout_completed.connect(self.refresh)
        app_signals.hotel_added.connect(self.refresh)
        
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header_layout = QHBoxLayout()
        header = QLabel("Hotels Module")
        header.setStyleSheet("font-size: 24px; font-weight: bold; padding: 16px;")
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search hotels or bookings...")
        self.search_input.setFixedWidth(300)
        self.search_input.textChanged.connect(self.on_search)
        
        header_layout.addWidget(header)
        header_layout.addStretch()
        header_layout.addWidget(self.search_input)
        layout.addLayout(header_layout)
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # --- Hotels Tab ---
        hotels_tab = QWidget()
        hotels_layout = QVBoxLayout(hotels_tab)
        
        btn_layout1 = QHBoxLayout()
        add_hotel_btn = QPushButton("+ Add Hotel")
        add_hotel_btn.clicked.connect(self._add_hotel)
        btn_layout1.addStretch()
        btn_layout1.addWidget(add_hotel_btn)
        hotels_layout.addLayout(btn_layout1)
        
        self.hotels_table = QTableWidget(0, 7)
        self.hotels_table.setHorizontalHeaderLabels(["Code", "Hotel Name", "City", "Country", "Stars", "Status", "Actions"])
        self.hotels_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.hotels_table.setAlternatingRowColors(True)
        self.hotels_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        hotels_layout.addWidget(self.hotels_table)
        
        hotel_pagination = QHBoxLayout()
        hotel_pagination.addStretch()
        self.btn_hotel_prev = QPushButton("< Prev")
        self.lbl_hotel_page = QLabel("Page 1 of 1")
        self.btn_hotel_next = QPushButton("Next >")
        self.btn_hotel_prev.clicked.connect(self._hotel_prev_page)
        self.btn_hotel_next.clicked.connect(self._hotel_next_page)
        hotel_pagination.addWidget(self.btn_hotel_prev)
        hotel_pagination.addWidget(self.lbl_hotel_page)
        hotel_pagination.addWidget(self.btn_hotel_next)
        hotel_pagination.addStretch()
        hotels_layout.addLayout(hotel_pagination)
        
        self.tabs.addTab(hotels_tab, "Hotel Directory")
        
        # --- Bookings Tab ---
        bookings_tab = QWidget()
        bookings_layout = QVBoxLayout(bookings_tab)
        
        btn_layout2 = QHBoxLayout()
        add_booking_btn = QPushButton("+ New Booking")
        add_booking_btn.clicked.connect(self._add_booking)
        btn_layout2.addStretch()
        btn_layout2.addWidget(add_booking_btn)
        bookings_layout.addLayout(btn_layout2)
        
        self.bookings_table = QTableWidget(0, 9)
        self.bookings_table.setHorizontalHeaderLabels(["Booking Ref", "Customer", "Hotel", "Check-In", "Check-Out", "Rooms", "Total Amount", "Status", "Actions"])
        self.bookings_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.bookings_table.setAlternatingRowColors(True)
        self.bookings_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        bookings_layout.addWidget(self.bookings_table)
        
        booking_pagination = QHBoxLayout()
        booking_pagination.addStretch()
        self.btn_booking_prev = QPushButton("< Prev")
        self.lbl_booking_page = QLabel("Page 1 of 1")
        self.btn_booking_next = QPushButton("Next >")
        self.btn_booking_prev.clicked.connect(self._booking_prev_page)
        self.btn_booking_next.clicked.connect(self._booking_next_page)
        booking_pagination.addWidget(self.btn_booking_prev)
        booking_pagination.addWidget(self.lbl_booking_page)
        booking_pagination.addWidget(self.btn_booking_next)
        booking_pagination.addStretch()
        bookings_layout.addLayout(booking_pagination)
        
        self.tabs.addTab(bookings_tab, "Bookings")

    def refresh(self):
        query = self.search_input.text()
        self.viewmodel.load_hotels(query=query, skip=(self.hotel_page - 1) * self.page_size, limit=self.page_size)
        self.viewmodel.load_bookings(query=query, skip=(self.booking_page - 1) * self.page_size, limit=self.page_size)
        
    def on_search(self):
        self.hotel_page = 1
        self.booking_page = 1
        self.refresh()
        
    def _hotel_prev_page(self):
        if self.hotel_page > 1:
            self.hotel_page -= 1
            self.refresh()
            
    def _hotel_next_page(self):
        import math
        if self.hotel_page < max(1, math.ceil(self.total_hotels / self.page_size)):
            self.hotel_page += 1
            self.refresh()
            
    def _booking_prev_page(self):
        if self.booking_page > 1:
            self.booking_page -= 1
            self.refresh()
            
    def _booking_next_page(self):
        import math
        if self.booking_page < max(1, math.ceil(self.total_bookings / self.page_size)):
            self.booking_page += 1
            self.refresh()

    def _on_hotels_loaded(self, result):
        self.total_hotels = result.get('total', 0)
        import math
        total_pages = max(1, math.ceil(self.total_hotels / self.page_size))
        self.lbl_hotel_page.setText(f"Page {self.hotel_page} of {total_pages}")
        self.btn_hotel_prev.setEnabled(self.hotel_page > 1)
        self.btn_hotel_next.setEnabled(self.hotel_page < total_pages)
        
        self.hotels_table.setRowCount(0)
        items = result.get('items', [])
        for row, hotel in enumerate(items):
            self.hotels_table.insertRow(row)
            self.hotels_table.setItem(row, 0, QTableWidgetItem(hotel.hotel_code))
            self.hotels_table.setItem(row, 1, QTableWidgetItem(hotel.hotel_name))
            self.hotels_table.setItem(row, 2, QTableWidgetItem(hotel.city))
            self.hotels_table.setItem(row, 3, QTableWidgetItem(hotel.country))
            
            star_item = QTableWidgetItem("★" * (hotel.star_rating or 0))
            star_item.setForeground(Qt.GlobalColor.yellow)
            self.hotels_table.setItem(row, 4, star_item)
            
            status_item = QTableWidgetItem(hotel.status)
            if hotel.status == "Active":
                status_item.setForeground(Qt.GlobalColor.green)
            else:
                status_item.setForeground(Qt.GlobalColor.gray)
            self.hotels_table.setItem(row, 5, status_item)
            
            edit_btn = QPushButton("Edit")
            edit_btn.setObjectName("btn_secondary")
            edit_btn.setEnabled(has_permission(self.current_user, Modules.HOTELS, Actions.EDIT))
            edit_btn.clicked.connect(lambda checked, h=hotel: self._edit_hotel(h))
            self.hotels_table.setCellWidget(row, 6, edit_btn)

    def _on_bookings_loaded(self, result):
        self.total_bookings = result.get('total', 0)
        import math
        total_pages = max(1, math.ceil(self.total_bookings / self.page_size))
        self.lbl_booking_page.setText(f"Page {self.booking_page} of {total_pages}")
        self.btn_booking_prev.setEnabled(self.booking_page > 1)
        self.btn_booking_next.setEnabled(self.booking_page < total_pages)
        
        self.bookings_table.setRowCount(0)
        items = result.get('items', [])
        for row, booking in enumerate(items):
            self.bookings_table.insertRow(row)
            self.bookings_table.setItem(row, 0, QTableWidgetItem(booking.booking_number))
            
            customer_name = booking.customer.full_name if booking.customer else "Unknown"
            self.bookings_table.setItem(row, 1, QTableWidgetItem(customer_name))
            
            hotel_name = booking.hotel.hotel_name if booking.hotel else "Unknown"
            self.bookings_table.setItem(row, 2, QTableWidgetItem(hotel_name))
            
            self.bookings_table.setItem(row, 3, QTableWidgetItem(str(booking.check_in_date)))
            self.bookings_table.setItem(row, 4, QTableWidgetItem(str(booking.check_out_date)))
            self.bookings_table.setItem(row, 5, QTableWidgetItem(f"{booking.num_rooms} ({booking.room_type})"))
            
            total_amt = format_currency(booking.total_selling)
            self.bookings_table.setItem(row, 6, QTableWidgetItem(total_amt))
            
            status_item = QTableWidgetItem(booking.status)
            if booking.status == "Confirmed":
                status_item.setForeground(Qt.GlobalColor.green)
            elif booking.status == "Pending":
                status_item.setForeground(Qt.GlobalColor.yellow)
            else:
                status_item.setForeground(Qt.GlobalColor.red)
            self.bookings_table.setItem(row, 7, status_item)
            
            edit_btn = QPushButton("Edit")
            edit_btn.setObjectName("btn_secondary")
            edit_btn.setEnabled(has_permission(self.current_user, Modules.HOTELS, Actions.EDIT))
            edit_btn.clicked.connect(lambda checked, b=booking: self._edit_booking(b))
            self.bookings_table.setCellWidget(row, 8, edit_btn)

    def _add_hotel(self):
        if not has_permission(self.current_user, Modules.HOTELS, Actions.ADD): return
        dialog = HotelForm(self.viewmodel, self.current_user.id, parent=self)
        if dialog.exec():
            self.refresh()
            
    def _edit_hotel(self, hotel):
        if not has_permission(self.current_user, Modules.HOTELS, Actions.EDIT): return
        dialog = HotelForm(self.viewmodel, self.current_user.id, hotel=hotel, parent=self)
        if dialog.exec():
            self.refresh()

    def _add_booking(self):
        dialog = HotelBookingForm(self.viewmodel, self.current_user.id, parent=self)
        if dialog.exec():
            self.refresh()
            
    def _edit_booking(self, booking):
        if not has_permission(self.current_user, Modules.HOTELS, Actions.EDIT): return
        dialog = HotelBookingForm(self.viewmodel, self.current_user.id, booking=booking, parent=self)
        if dialog.exec():
            self.refresh()

    def _on_error(self, msg):
        QMessageBox.critical(self, "Error", msg)
