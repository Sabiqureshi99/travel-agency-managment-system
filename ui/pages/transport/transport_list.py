from core.permissions import has_permission, Modules, Actions
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QTabWidget, QTableWidget, QTableWidgetItem,
                               QHeaderView, QMessageBox, QAbstractItemView)
from PySide6.QtCore import Qt
from utils.formatters import format_currency

class TransportListPage(QWidget):
    def __init__(self, current_user, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        
        self.veh_page = 1
        self.drv_page = 1
        self.bkg_page = 1
        self.page_size = 50
        
        self.total_veh = 0
        self.total_drv = 0
        self.total_bkg = 0
        
        self._setup_ui()
        self._load_data()
        
        # Connect global signals for background refresh
        from core.signals import app_signals
        app_signals.umrah_checkout_completed.connect(self._load_data)
        app_signals.transport_added.connect(self._load_data)
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        header = QHBoxLayout()
        title = QLabel("Transport Management")
        title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 16px;")
        
        self.btn_refresh = QPushButton("Refresh")
        self.btn_add_veh = QPushButton("+ Add Vehicle")
        self.btn_add_drv = QPushButton("+ Add Driver")
        self.btn_add_bkg = QPushButton("+ Add Booking")
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.btn_refresh)
        header.addWidget(self.btn_add_veh)
        header.addWidget(self.btn_add_drv)
        header.addWidget(self.btn_add_bkg)
        layout.addLayout(header)
        
        # Wrapping tabs with margin
        tabs_layout = QVBoxLayout()
        tabs_layout.setContentsMargins(16, 0, 16, 16)
        
        self.tabs = QTabWidget()
        
        # Vehicles
        tab_veh = QWidget()
        l_veh = QVBoxLayout(tab_veh)
        self.tbl_veh = QTableWidget(0, 7)
        self.tbl_veh.setHorizontalHeaderLabels([
            "Reg#", "Type", "Make", "Model", "Capacity", "Status", "Actions"
        ])
        self.tbl_veh.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_veh.setAlternatingRowColors(True)
        self.tbl_veh.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        l_veh.addWidget(self.tbl_veh)
        
        veh_pagination = QHBoxLayout()
        veh_pagination.addStretch()
        self.btn_veh_prev = QPushButton("< Prev")
        self.lbl_veh_page = QLabel("Page 1 of 1")
        self.btn_veh_next = QPushButton("Next >")
        self.btn_veh_prev.clicked.connect(self._veh_prev_page)
        self.btn_veh_next.clicked.connect(self._veh_next_page)
        veh_pagination.addWidget(self.btn_veh_prev)
        veh_pagination.addWidget(self.lbl_veh_page)
        veh_pagination.addWidget(self.btn_veh_next)
        veh_pagination.addStretch()
        l_veh.addLayout(veh_pagination)
        
        self.tabs.addTab(tab_veh, "Vehicles")
        
        # Drivers
        tab_drv = QWidget()
        l_drv = QVBoxLayout(tab_drv)
        self.tbl_drv = QTableWidget(0, 7)
        self.tbl_drv.setHorizontalHeaderLabels([
            "Code", "Name", "Phone", "License", "Expiry", "Status", "Actions"
        ])
        self.tbl_drv.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_drv.setAlternatingRowColors(True)
        self.tbl_drv.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        l_drv.addWidget(self.tbl_drv)
        
        drv_pagination = QHBoxLayout()
        drv_pagination.addStretch()
        self.btn_drv_prev = QPushButton("< Prev")
        self.lbl_drv_page = QLabel("Page 1 of 1")
        self.btn_drv_next = QPushButton("Next >")
        self.btn_drv_prev.clicked.connect(self._drv_prev_page)
        self.btn_drv_next.clicked.connect(self._drv_next_page)
        drv_pagination.addWidget(self.btn_drv_prev)
        drv_pagination.addWidget(self.lbl_drv_page)
        drv_pagination.addWidget(self.btn_drv_next)
        drv_pagination.addStretch()
        l_drv.addLayout(drv_pagination)
        
        self.tabs.addTab(tab_drv, "Drivers")
        
        # Bookings
        tab_bkg = QWidget()
        l_bkg = QVBoxLayout(tab_bkg)
        self.tbl_bkg = QTableWidget(0, 9)
        self.tbl_bkg.setHorizontalHeaderLabels([
            "Number", "Vehicle", "Driver", "Customer", "Date", "Route", "Amount", "Status", "Actions"
        ])
        self.tbl_bkg.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_bkg.setAlternatingRowColors(True)
        self.tbl_bkg.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        l_bkg.addWidget(self.tbl_bkg)
        
        bkg_pagination = QHBoxLayout()
        bkg_pagination.addStretch()
        self.btn_bkg_prev = QPushButton("< Prev")
        self.lbl_bkg_page = QLabel("Page 1 of 1")
        self.btn_bkg_next = QPushButton("Next >")
        self.btn_bkg_prev.clicked.connect(self._bkg_prev_page)
        self.btn_bkg_next.clicked.connect(self._bkg_next_page)
        bkg_pagination.addWidget(self.btn_bkg_prev)
        bkg_pagination.addWidget(self.lbl_bkg_page)
        bkg_pagination.addWidget(self.btn_bkg_next)
        bkg_pagination.addStretch()
        l_bkg.addLayout(bkg_pagination)
        
        self.tabs.addTab(tab_bkg, "Bookings")
        
        tabs_layout.addWidget(self.tabs)
        layout.addLayout(tabs_layout)
        
        # Connections
        self.btn_refresh.clicked.connect(self.refresh)
        self.btn_add_veh.clicked.connect(self._add_vehicle)
        self.btn_add_drv.clicked.connect(self._add_driver)
        self.btn_add_bkg.clicked.connect(self._add_booking)
        
    def _load_data(self):
        from viewmodels.transport_viewmodel import TransportViewModel
        if not hasattr(self, 'viewmodel'):
            self.viewmodel = TransportViewModel()
            self.viewmodel.vehicles_loaded.connect(self._on_vehicles_loaded)
            self.viewmodel.drivers_loaded.connect(self._on_drivers_loaded)
            self.viewmodel.bookings_loaded.connect(self._on_bookings_loaded)
            
            self.viewmodel.vehicle_saved.connect(lambda _: self.viewmodel.load_vehicles())
            self.viewmodel.driver_saved.connect(lambda _: self.viewmodel.load_drivers())
            self.viewmodel.booking_saved.connect(lambda _: self.viewmodel.load_bookings())
            self.viewmodel.error_occurred.connect(self._on_error)
            
        self.viewmodel.load_vehicles(skip=(self.veh_page - 1) * self.page_size, limit=self.page_size)
        self.viewmodel.load_drivers(skip=(self.drv_page - 1) * self.page_size, limit=self.page_size)
        self.viewmodel.load_bookings(skip=(self.bkg_page - 1) * self.page_size, limit=self.page_size)
        
    def refresh(self):
        self._load_data()

    def _veh_prev_page(self):
        if self.veh_page > 1:
            self.veh_page -= 1
            self.refresh()
            
    def _veh_next_page(self):
        import math
        if self.veh_page < max(1, math.ceil(self.total_veh / self.page_size)):
            self.veh_page += 1
            self.refresh()
            
    def _drv_prev_page(self):
        if self.drv_page > 1:
            self.drv_page -= 1
            self.refresh()
            
    def _drv_next_page(self):
        import math
        if self.drv_page < max(1, math.ceil(self.total_drv / self.page_size)):
            self.drv_page += 1
            self.refresh()
            
    def _bkg_prev_page(self):
        if self.bkg_page > 1:
            self.bkg_page -= 1
            self.refresh()
            
    def _bkg_next_page(self):
        import math
        if self.bkg_page < max(1, math.ceil(self.total_bkg / self.page_size)):
            self.bkg_page += 1
            self.refresh()

    def _on_vehicles_loaded(self, result):
        self.total_veh = result.get('total', 0)
        import math
        total_pages = max(1, math.ceil(self.total_veh / self.page_size))
        self.lbl_veh_page.setText(f"Page {self.veh_page} of {total_pages}")
        self.btn_veh_prev.setEnabled(self.veh_page > 1)
        self.btn_veh_next.setEnabled(self.veh_page < total_pages)
        
        vehicles = result.get('vehicles', [])
        self.tbl_veh.setRowCount(0)
        self._vehicles = vehicles
        for i, v in enumerate(vehicles):
            self.tbl_veh.insertRow(i)
            self.tbl_veh.setItem(i, 0, QTableWidgetItem(getattr(v, 'registration_number', '')))
            self.tbl_veh.setItem(i, 1, QTableWidgetItem(getattr(v, 'vehicle_type', '')))
            self.tbl_veh.setItem(i, 2, QTableWidgetItem(getattr(v, 'make', '')))
            self.tbl_veh.setItem(i, 3, QTableWidgetItem(getattr(v, 'model', '')))
            self.tbl_veh.setItem(i, 4, QTableWidgetItem(str(getattr(v, 'capacity', ''))))
            
            status = getattr(v, 'status', '')
            status_item = QTableWidgetItem(status)
            if status == "Available":
                status_item.setForeground(Qt.GlobalColor.green)
            elif status == "Inactive":
                status_item.setForeground(Qt.GlobalColor.red)
            else:
                status_item.setForeground(Qt.GlobalColor.darkYellow)
            self.tbl_veh.setItem(i, 5, status_item)
            
            edit_btn = QPushButton("Edit")
            edit_btn.setObjectName("btn_secondary")
            edit_btn.setEnabled(has_permission(self.current_user, Modules.TRANSPORT, Actions.EDIT))
            edit_btn.clicked.connect(lambda checked, idx=i: self._edit_vehicle(idx))
            self.tbl_veh.setCellWidget(i, 6, edit_btn)

    def _on_drivers_loaded(self, result):
        self.total_drv = result.get('total', 0)
        import math
        total_pages = max(1, math.ceil(self.total_drv / self.page_size))
        self.lbl_drv_page.setText(f"Page {self.drv_page} of {total_pages}")
        self.btn_drv_prev.setEnabled(self.drv_page > 1)
        self.btn_drv_next.setEnabled(self.drv_page < total_pages)
        
        drivers = result.get('drivers', [])
        self.tbl_drv.setRowCount(0)
        self._drivers = drivers
        for i, d in enumerate(drivers):
            self.tbl_drv.insertRow(i)
            self.tbl_drv.setItem(i, 0, QTableWidgetItem(getattr(d, 'employee_id', 'N/A')))
            self.tbl_drv.setItem(i, 1, QTableWidgetItem(getattr(d, 'full_name', '')))
            self.tbl_drv.setItem(i, 2, QTableWidgetItem(getattr(d, 'phone', '')))
            self.tbl_drv.setItem(i, 3, QTableWidgetItem(getattr(d, 'license_number', '')))
            self.tbl_drv.setItem(i, 4, QTableWidgetItem(str(getattr(d, 'license_expiry', ''))))
            
            status = getattr(d, 'status', '')
            status_item = QTableWidgetItem(status)
            if status == "Available":
                status_item.setForeground(Qt.GlobalColor.green)
            elif status == "Inactive":
                status_item.setForeground(Qt.GlobalColor.red)
            else:
                status_item.setForeground(Qt.GlobalColor.darkYellow)
            self.tbl_drv.setItem(i, 5, status_item)
            
            edit_btn = QPushButton("Edit")
            edit_btn.setObjectName("btn_secondary")
            edit_btn.setEnabled(has_permission(self.current_user, Modules.TRANSPORT, Actions.EDIT))
            edit_btn.clicked.connect(lambda checked, idx=i: self._edit_driver(idx))
            self.tbl_drv.setCellWidget(i, 6, edit_btn)

    def _on_bookings_loaded(self, result):
        self.total_bkg = result.get('total', 0)
        import math
        total_pages = max(1, math.ceil(self.total_bkg / self.page_size))
        self.lbl_bkg_page.setText(f"Page {self.bkg_page} of {total_pages}")
        self.btn_bkg_prev.setEnabled(self.bkg_page > 1)
        self.btn_bkg_next.setEnabled(self.bkg_page < total_pages)
        
        bookings = result.get('bookings', [])
        self.tbl_bkg.setRowCount(0)
        self._bookings = bookings
        for i, b in enumerate(bookings):
            self.tbl_bkg.insertRow(i)
            self.tbl_bkg.setItem(i, 0, QTableWidgetItem(getattr(b, 'booking_number', '')))
            
            veh = getattr(b, 'vehicle', None)
            veh_name = f"{veh.registration_number}" if veh else ""
            self.tbl_bkg.setItem(i, 1, QTableWidgetItem(veh_name))
            
            drv = getattr(b, 'driver', None)
            drv_name = f"{drv.full_name}" if drv else ""
            self.tbl_bkg.setItem(i, 2, QTableWidgetItem(drv_name))
            
            cust = getattr(b, 'customer', None)
            cust_name = cust.full_name if cust else ""
            self.tbl_bkg.setItem(i, 3, QTableWidgetItem(cust_name))
            
            date_str = f"{getattr(b, 'pickup_date', '')} {getattr(b, 'pickup_time', '')}"
            self.tbl_bkg.setItem(i, 4, QTableWidgetItem(date_str))
            
            route_str = f"{getattr(b, 'pickup_location', '')} -> {getattr(b, 'dropoff_location', '')}"
            self.tbl_bkg.setItem(i, 5, QTableWidgetItem(route_str))
            
            amount = getattr(b, 'total_amount', 0)
            self.tbl_bkg.setItem(i, 6, QTableWidgetItem(format_currency(amount)))
            
            status = getattr(b, 'status', '')
            status_item = QTableWidgetItem(status)
            if status == "Confirmed" or status == "Completed":
                status_item.setForeground(Qt.GlobalColor.green)
            elif status == "Cancelled":
                status_item.setForeground(Qt.GlobalColor.red)
            else:
                status_item.setForeground(Qt.GlobalColor.darkYellow)
            self.tbl_bkg.setItem(i, 7, status_item)
            
            edit_btn = QPushButton("Edit")
            edit_btn.setObjectName("btn_secondary")
            edit_btn.setEnabled(has_permission(self.current_user, Modules.TRANSPORT, Actions.EDIT))
            edit_btn.clicked.connect(lambda checked, idx=i: self._edit_booking(idx))
            self.tbl_bkg.setCellWidget(i, 8, edit_btn)

    def _on_error(self, message):
        QMessageBox.warning(self, "Error", message)

    def _add_vehicle(self):
        if not has_permission(self.current_user, Modules.TRANSPORT, Actions.ADD): return
        from ui.pages.transport.transport_form import VehicleForm
        dialog = VehicleForm(self.viewmodel, self.current_user.id, parent=self)
        dialog.exec()
        
    def _add_driver(self):
        if not has_permission(self.current_user, Modules.TRANSPORT, Actions.ADD): return
        from ui.pages.transport.transport_form import DriverForm
        dialog = DriverForm(self.viewmodel, self.current_user.id, parent=self)
        dialog.exec()
        
    def _add_booking(self):
        from ui.pages.transport.transport_form import TransportBookingForm
        dialog = TransportBookingForm(self.viewmodel, self.current_user.id, parent=self)
        dialog.exec()
        
    def _edit_vehicle(self, idx):
        if not hasattr(self, '_vehicles'): return
        v = self._vehicles[idx]
        from ui.pages.transport.transport_form import VehicleForm
        dialog = VehicleForm(self.viewmodel, self.current_user.id, vehicle=v, parent=self)
        dialog.exec()

    def _edit_driver(self, idx):
        if not hasattr(self, '_drivers'): return
        d = self._drivers[idx]
        from ui.pages.transport.transport_form import DriverForm
        dialog = DriverForm(self.viewmodel, self.current_user.id, driver=d, parent=self)
        dialog.exec()
        
    def _edit_booking(self, idx):
        if not hasattr(self, '_bookings'): return
        b = self._bookings[idx]
        from ui.pages.transport.transport_form import TransportBookingForm
        dialog = TransportBookingForm(self.viewmodel, self.current_user.id, booking=b, parent=self)
        dialog.exec()
