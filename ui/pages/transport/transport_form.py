from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QComboBox, QPushButton, QFormLayout, 
                               QDateEdit, QSpinBox, QMessageBox, QGroupBox, QDoubleSpinBox, QTimeEdit)
from PySide6.QtCore import QDate, Qt, QTime
from utils.formatters import format_currency
from ui.components.searchable_combo_box import SearchableComboBox

class VehicleForm(QDialog):
    def __init__(self, viewmodel, current_user_id, vehicle=None, parent=None):
        super().__init__(parent)
        self.viewmodel = viewmodel
        self.current_user_id = current_user_id
        self.vehicle = vehicle
        self.setWindowTitle("Add/Edit Vehicle")
        self.setMinimumWidth(500)
        
        self.viewmodel.vehicle_saved.connect(self._on_saved)
        
        self._setup_ui()
        if self.vehicle:
            self._populate_fields()
            
    def _setup_ui(self):
        main = QVBoxLayout(self)
        main.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        group = QGroupBox("Vehicle Details")
        group.setMaximumWidth(600)
        form = QFormLayout(group)
        form.setSpacing(15)
        
        self.reg_no = QLineEdit()
        self.make = QLineEdit()
        self.model = QLineEdit()
        self.year = QSpinBox()
        self.year.setRange(1990, 2100)
        self.year.setValue(QDate.currentDate().year())
        self.v_type = QComboBox()
        self.v_type.addItems(["Sedan", "SUV", "Hiace", "Coaster", "Bus"])
        self.capacity = QSpinBox()
        self.capacity.setRange(1, 100)
        self.capacity.setValue(4)
        self.status = QComboBox()
        self.status.addItems(["Available", "In Use", "Maintenance", "Inactive"])
        
        form.addRow("Registration # *:", self.reg_no)
        form.addRow("Make *:", self.make)
        form.addRow("Model *:", self.model)
        form.addRow("Year:", self.year)
        form.addRow("Type:", self.v_type)
        form.addRow("Capacity (Seats):", self.capacity)
        form.addRow("Status:", self.status)
        
        main.addWidget(group)
        
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Save Vehicle")
        btn_save.setShortcut("Return")
        btn_save.setDefault(True)
        btn_cancel = QPushButton("Cancel")
        btn_save.clicked.connect(self._save)
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        main.addLayout(btn_layout)
        
    def _populate_fields(self):
        self.reg_no.setText(self.vehicle.registration_number)
        self.make.setText(self.vehicle.make)
        self.model.setText(self.vehicle.model)
        if self.vehicle.year:
            self.year.setValue(self.vehicle.year)
        self.v_type.setCurrentText(self.vehicle.vehicle_type)
        self.capacity.setValue(self.vehicle.capacity)
        self.status.setCurrentText(self.vehicle.status)
        
    def _save(self):
        if not self.reg_no.text().strip() or not self.make.text().strip() or not self.model.text().strip():
            QMessageBox.warning(self, "Validation Error", "Registration #, Make, and Model are required.")
            return
            
        data = {
            "id": self.vehicle.id if self.vehicle else None,
            "registration_number": self.reg_no.text().strip(),
            "make": self.make.text().strip(),
            "model": self.model.text().strip(),
            "year": self.year.value(),
            "vehicle_type": self.v_type.currentText(),
            "capacity": self.capacity.value(),
            "status": self.status.currentText()
        }
        self.viewmodel.save_vehicle(data, self.current_user_id)
        
    def _on_saved(self, result):
        self.accept()


class DriverForm(QDialog):
    def __init__(self, viewmodel, current_user_id, driver=None, parent=None):
        super().__init__(parent)
        self.viewmodel = viewmodel
        self.current_user_id = current_user_id
        self.driver = driver
        self.setWindowTitle("Add/Edit Driver")
        self.setMinimumWidth(500)
        
        self.viewmodel.driver_saved.connect(self._on_saved)
        
        self._setup_ui()
        if self.driver:
            self._populate_fields()
            
    def _setup_ui(self):
        main = QVBoxLayout(self)
        main.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        group = QGroupBox("Driver Details")
        group.setMaximumWidth(600)
        form = QFormLayout(group)
        form.setSpacing(15)
        
        self.full_name = QLineEdit()
        self.phone = QLineEdit()
        self.license = QLineEdit()
        self.l_type = QComboBox()
        self.l_type.addItems(["LTV", "HTV", "PSV"])
        self.expiry = QDateEdit(QDate.currentDate().addYears(1))
        self.expiry.setCalendarPopup(True)
        self.status = QComboBox()
        self.status.addItems(["Available", "On Trip", "On Leave", "Inactive"])
        
        form.addRow("Full Name *:", self.full_name)
        form.addRow("Phone *:", self.phone)
        form.addRow("License Number *:", self.license)
        form.addRow("License Type:", self.l_type)
        form.addRow("License Expiry:", self.expiry)
        form.addRow("Status:", self.status)
        
        main.addWidget(group)
        
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Save Driver")
        btn_save.setShortcut("Return")
        btn_save.setDefault(True)
        btn_cancel = QPushButton("Cancel")
        btn_save.clicked.connect(self._save)
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        main.addLayout(btn_layout)
        
    def _populate_fields(self):
        self.full_name.setText(self.driver.full_name)
        self.phone.setText(self.driver.phone)
        self.license.setText(self.driver.license_number)
        self.l_type.setCurrentText(self.driver.license_type)
        if self.driver.license_expiry:
            self.expiry.setDate(self.driver.license_expiry)
        self.status.setCurrentText(self.driver.status)
        
    def _save(self):
        if not self.full_name.text().strip() or not self.phone.text().strip() or not self.license.text().strip():
            QMessageBox.warning(self, "Validation Error", "Name, Phone, and License Number are required.")
            return
            
        data = {
            "id": self.driver.id if self.driver else None,
            "full_name": self.full_name.text().strip(),
            "phone": self.phone.text().strip(),
            "license_number": self.license.text().strip(),
            "license_type": self.l_type.currentText(),
            "license_expiry": self.expiry.date().toPython(),
            "status": self.status.currentText()
        }
        self.viewmodel.save_driver(data, self.current_user_id)
        
    def _on_saved(self, result):
        self.accept()


class TransportBookingForm(QDialog):
    def __init__(self, viewmodel, current_user_id, booking=None, parent=None):
        super().__init__(parent)
        self.viewmodel = viewmodel
        self.current_user_id = current_user_id
        self.booking = booking
        self.setWindowTitle("Add/Edit Transport Booking")
        self.setMinimumWidth(600)
        
        self.viewmodel.booking_saved.connect(self._on_saved)
        self.viewmodel.form_data_loaded.connect(self._on_data_loaded)
        
        self.customer_map = {}
        self.vehicle_map = {}
        self.driver_map = {}
        
        self._setup_ui()
        
        # Load dropdowns asynchronously
        self.customer_cb.search_input.setText("Loading customers...")
        self.vehicle_cb.search_input.setText("Loading vehicles...")
        self.driver_cb.search_input.setText("Loading drivers...")
        self.customer_cb.setEnabled(False)
        self.vehicle_cb.setEnabled(False)
        self.driver_cb.setEnabled(False)
        self.viewmodel.load_form_data()
        
    def _setup_ui(self):
        main = QVBoxLayout(self)
        main.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Details Group
        g1 = QGroupBox("Booking & Route Details")
        g1.setMaximumWidth(600)
        l1 = QFormLayout(g1)
        l1.setSpacing(15)
        
        self.customer_cb = SearchableComboBox()
        self.customer_cb.search_input.setPlaceholderText("Search Customer...")
        self.vehicle_cb = SearchableComboBox()
        self.vehicle_cb.search_input.setPlaceholderText("Search Vehicle...")
        self.driver_cb = SearchableComboBox()
        self.driver_cb.search_input.setPlaceholderText("Search Driver...")
        
        self.pickup_loc = QLineEdit()
        self.dropoff_loc = QLineEdit()
        
        self.bkg_date = QDateEdit(QDate.currentDate())
        self.bkg_date.setCalendarPopup(True)
        
        self.pickup_date = QDateEdit(QDate.currentDate().addDays(1))
        self.pickup_date.setCalendarPopup(True)
        
        self.pickup_time = QTimeEdit(QTime(10, 0))
        self.return_date = QDateEdit(QDate.currentDate().addDays(1))
        self.return_date.setCalendarPopup(True)
        
        self.status = QComboBox()
        self.status.addItems(["Confirmed", "Completed", "Cancelled"])
        
        l1.addRow("Customer *:", self.customer_cb)
        l1.addRow("Vehicle:", self.vehicle_cb)
        l1.addRow("Driver:", self.driver_cb)
        l1.addRow("Pickup Location *:", self.pickup_loc)
        l1.addRow("Dropoff Location *:", self.dropoff_loc)
        l1.addRow("Booking Date:", self.bkg_date)
        l1.addRow("Pickup Date:", self.pickup_date)
        l1.addRow("Pickup Time:", self.pickup_time)
        l1.addRow("Return Date (Optional):", self.return_date)
        l1.addRow("Status:", self.status)
        
        main.addWidget(g1)
        
        # Financials
        g2 = QGroupBox("Financials")
        g2.setMaximumWidth(600)
        l2 = QFormLayout(g2)
        l2.setSpacing(15)
        
        self.cost_amount = QDoubleSpinBox()
        self.cost_amount.setRange(0, 10000000)
        self.cost_amount.setPrefix("PKR ")
        
        self.total_amount = QDoubleSpinBox()
        self.total_amount.setRange(0, 10000000)
        self.total_amount.setPrefix("PKR ")
        
        l2.addRow("Cost Amount (Buying) *:", self.cost_amount)
        l2.addRow("Total Amount (Selling) *:", self.total_amount)
        main.addWidget(g2)
        
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Save Booking")
        btn_save.setShortcut("Return")
        btn_save.setDefault(True)
        btn_cancel = QPushButton("Cancel")
        btn_save.clicked.connect(self._save)
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        main.addLayout(btn_layout)
        
    def _on_data_loaded(self, result):
        self.customer_cb.search_input.clear()
        self.vehicle_cb.search_input.clear()
        self.driver_cb.search_input.clear()
        
        customers = result.get('customers', [])
        vehicles = result.get('vehicles', [])
        drivers = result.get('drivers', [])
        
        self.customer_map = {c.full_name: c.id for c in customers}
        if self.customer_map:
            self.customer_cb.set_data([(c.full_name, c.id) for c in customers])
            self.customer_cb.setEnabled(True)
        else:
            self.customer_cb.search_input.setText("No customers found")
            
        self.vehicle_map = {f"{v.registration_number} - {v.make} {v.model}": v.id for v in vehicles}
        if self.vehicle_map:
            self.vehicle_cb.set_data([(k, v) for k, v in self.vehicle_map.items()])
            self.vehicle_cb.setEnabled(True)
            
        self.driver_map = {d.full_name: d.id for d in drivers}
        if self.driver_map:
            self.driver_cb.set_data([(k, v) for k, v in self.driver_map.items()])
            self.driver_cb.setEnabled(True)
            
        if self.booking:
            if self.booking.customer:
                self.customer_cb.search_input.setText(self.booking.customer.full_name)
            if self.booking.vehicle:
                v_str = f"{self.booking.vehicle.registration_number} - {self.booking.vehicle.make} {self.booking.vehicle.model}"
                self.vehicle_cb.search_input.setText(v_str)
            if self.booking.driver:
                self.driver_cb.search_input.setText(self.booking.driver.full_name)
                
            self.pickup_loc.setText(self.booking.pickup_location)
            self.dropoff_loc.setText(self.booking.dropoff_location)
            self.bkg_date.setDate(self.booking.booking_date)
            self.pickup_date.setDate(self.booking.pickup_date)
            
            # parse time string
            try:
                t = QTime.fromString(self.booking.pickup_time, "HH:mm")
                if t.isValid():
                    self.pickup_time.setTime(t)
            except: pass
            
            if self.booking.return_date:
                self.return_date.setDate(self.booking.return_date)
            
            self.total_amount.setValue(float(self.booking.total_amount))
            self.status.setCurrentText(self.booking.status)
        
    def _save(self):
        c_name = self.customer_cb.search_input.text()
        if not c_name or not self.customer_cb.isEnabled() or not self.pickup_loc.text().strip() or not self.dropoff_loc.text().strip():
            QMessageBox.warning(self, "Validation Error", "Customer, Pickup and Dropoff locations are required.")
            return
            
        v_name = self.vehicle_cb.search_input.text()
        d_name = self.driver_cb.search_input.text()
        
        data = {
            "id": self.booking.id if self.booking else None,
            "customer_id": self.customer_map.get(c_name, ""),
            "vehicle_id": self.vehicle_map.get(v_name, None) if v_name in self.vehicle_map else None,
            "driver_id": self.driver_map.get(d_name, None) if d_name in self.driver_map else None,
            "booking_date": self.bkg_date.date().toPython(),
            "pickup_location": self.pickup_loc.text().strip(),
            "dropoff_location": self.dropoff_loc.text().strip(),
            "pickup_date": self.pickup_date.date().toPython(),
            "pickup_time": self.pickup_time.time().toString("HH:mm"),
            "return_date": self.return_date.date().toPython(),
            "total_amount": self.total_amount.value(),
            "status": self.status.currentText()
        }
        self.viewmodel.save_booking(data, self.current_user_id)
        
    def _on_saved(self, result):
        try:
            from services.accounting_service import AccountingService
            from config.database import get_session
            from models.transport import TransportBooking
            from models.booking import Booking
            
            with get_session() as session:
                trans_b = session.query(TransportBooking).get(result.id)
                if trans_b:
                    central = Booking(
                        booking_type='Transport_Only',
                        customer_id=trans_b.customer_id,
                        cost_price=self.cost_amount.value(),
                        selling_price=trans_b.total_amount,
                        details=f"Transport Booking - Pickup: {trans_b.pickup_location}"
                    )
                    session.add(central)
                    session.commit()
                    
                    if trans_b.total_amount > 0:
                        invoice = AccountingService().post_standalone_booking(
                            customer_id=trans_b.customer_id,
                            total_amount=trans_b.total_amount,
                            item_description=f"Transport Booking - Pickup: {trans_b.pickup_location} - Dropoff: {trans_b.dropoff_location}",
                            created_by=self.current_user_id
                        )
                        
                        import os
                        import datetime
                        from services.invoice_generator import InvoiceGenerator
                        from utils.pdf_generator import VoucherBuilder
                        
                        os.makedirs("invoices", exist_ok=True)
                        inv_path = os.path.abspath(f"invoices/Invoice_{invoice.invoice_number}.pdf")
                        InvoiceGenerator.generate_invoice_pdf(invoice, inv_path)
                        if hasattr(os, 'startfile'):
                            os.startfile(inv_path)
                            
                        # Generate Voucher PDF
                        customer_name = trans_b.customer.full_name if trans_b.customer else "Unknown Customer"
                        customer_passport = trans_b.customer.passport_number if trans_b.customer else ""
                        
                        vehicle_str = f"{trans_b.vehicle.make} {trans_b.vehicle.model}" if trans_b.vehicle else ""
                        
                        v_data = {
                            'voucher_no': f"TV-{str(trans_b.id)[:6].upper()}",
                            'issue_date': datetime.datetime.now().strftime("%d/%m/%Y"),
                            'pkg_category': 'TRANSPORT ONLY',
                            'print_dt': datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                            'branch_office': 'MAIN OFFICE',
                            'passengers': [
                                {'name': customer_name, 'passport': customer_passport, 'group': ''}
                            ],
                            'accommodation': [],
                            'transport': [
                                {
                                    'date': trans_b.pickup_date.strftime("%d/%m/%Y") if hasattr(trans_b.pickup_date, 'strftime') else str(trans_b.pickup_date),
                                    'time': trans_b.pickup_time,
                                    'sector': f"{trans_b.pickup_location} TO {trans_b.dropoff_location}",
                                    'vehicle': vehicle_str
                                }
                            ],
                            'flights': []
                        }
                        
                        filename = f"Transport_Voucher_{str(trans_b.id)[:8]}.pdf"
                        voucher_path = VoucherBuilder(v_data, filename=filename).generate()
                        if hasattr(os, 'startfile'):
                            os.startfile(voucher_path)

                    from core.signals import app_signals
                    app_signals.dashboard_refresh_needed.emit()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save centralized booking or generate invoice/voucher: {str(e)}")
        self.accept()
