from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QComboBox, QPushButton, QFormLayout, 
                               QDateEdit, QSpinBox, QMessageBox, QGroupBox, QDoubleSpinBox)
from PySide6.QtCore import QDate, Qt
from utils.formatters import format_currency
from ui.components.searchable_combo_box import SearchableComboBox

class HotelForm(QDialog):
    def __init__(self, viewmodel, current_user_id, hotel=None, parent=None):
        super().__init__(parent)
        self.viewmodel = viewmodel
        self.current_user_id = current_user_id
        self.hotel = hotel
        self.setWindowTitle("Add/Edit Hotel Profile")
        self.setMinimumWidth(500)
        
        self.viewmodel.hotel_saved.connect(self._on_saved)
        
        self._setup_ui()
        if self.hotel:
            self._populate_fields()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Group Box
        group = QGroupBox("Hotel Details")
        group.setMaximumWidth(600)
        form = QFormLayout(group)
        form.setSpacing(15)
        
        self.hotel_name = QLineEdit()
        self.city = QLineEdit()
        self.country = QLineEdit("Pakistan")
        self.star_rating = QComboBox()
        self.star_rating.addItems(["1", "2", "3", "4", "5"])
        self.phone = QLineEdit()
        self.email = QLineEdit()
        self.status = QComboBox()
        self.status.addItems(["Active", "Inactive"])
        
        form.addRow("Hotel Name *:", self.hotel_name)
        form.addRow("City *:", self.city)
        form.addRow("Country *:", self.country)
        form.addRow("Star Rating:", self.star_rating)
        form.addRow("Phone:", self.phone)
        form.addRow("Email:", self.email)
        form.addRow("Status:", self.status)
        
        layout.addWidget(group)
        
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Save Hotel")
        btn_save.setShortcut("Return")
        btn_save.setDefault(True)
        btn_cancel = QPushButton("Cancel")
        btn_save.clicked.connect(self._save)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        
        layout.addLayout(btn_layout)

    def _populate_fields(self):
        self.hotel_name.setText(self.hotel.hotel_name)
        self.city.setText(self.hotel.city)
        self.country.setText(self.hotel.country)
        self.star_rating.setCurrentText(str(self.hotel.star_rating or 1))
        self.phone.setText(self.hotel.phone or "")
        self.email.setText(self.hotel.email or "")
        self.status.setCurrentText(self.hotel.status)
        
    def _save(self):
        if not self.hotel_name.text().strip() or not self.city.text().strip() or not self.country.text().strip():
            QMessageBox.warning(self, "Validation Error", "Hotel Name, City, and Country are required fields.")
            return

        data = {
            "id": self.hotel.id if self.hotel else None,
            "hotel_name": self.hotel_name.text().strip(),
            "city": self.city.text().strip(),
            "country": self.country.text().strip(),
            "star_rating": int(self.star_rating.currentText()),
            "phone": self.phone.text().strip(),
            "email": self.email.text().strip(),
            "status": self.status.currentText()
        }
        self.viewmodel.save_hotel(data, self.current_user_id)
        
    def _on_saved(self, result):
        self.accept()

class HotelBookingForm(QDialog):
    def __init__(self, viewmodel, current_user_id, booking=None, parent=None):
        super().__init__(parent)
        self.viewmodel = viewmodel
        self.current_user_id = current_user_id
        self.booking = booking
        self.setWindowTitle("New Hotel Booking" if not booking else "Edit Hotel Booking")
        self.setMinimumWidth(600)
        
        self.viewmodel.booking_saved.connect(self._on_saved)
        self.viewmodel.form_data_loaded.connect(self._on_data_loaded)
        
        self.customer_map = {}
        self.hotel_map = {}
        
        self._setup_ui()
        
        # Load dropdowns asynchronously
        self.customer_cb.search_input.setText("Loading customers...")
        self.hotel_cb.search_input.setText("Loading hotels...")
        self.customer_cb.setEnabled(False)
        self.hotel_cb.setEnabled(False)
        self.viewmodel.load_form_data()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Details Group
        details_group = QGroupBox("Booking Details")
        details_group.setMaximumWidth(600)
        form = QFormLayout(details_group)
        form.setSpacing(15)
        
        self.customer_cb = SearchableComboBox()
        self.customer_cb.search_input.setPlaceholderText("Search Customer...")
        self.hotel_cb = SearchableComboBox()
        self.hotel_cb.search_input.setPlaceholderText("Search Hotel...")
        self.check_in_date = QDateEdit(QDate.currentDate())
        self.check_in_date.setCalendarPopup(True)
        self.check_out_date = QDateEdit(QDate.currentDate().addDays(1))
        self.check_out_date.setCalendarPopup(True)
        
        self.nights = QSpinBox()
        self.nights.setRange(1, 365)
        self.nights.setValue(1)
        self.room_type = QComboBox()
        self.room_type.addItems(["Single", "Double", "Triple", "Quad", "Suite"])
        self.num_rooms = QSpinBox()
        self.num_rooms.setMinimum(1)
        self.status = QComboBox()
        self.status.addItems(["Confirmed", "Pending", "Cancelled"])
        
        form.addRow("Customer *:", self.customer_cb)
        form.addRow("Hotel *:", self.hotel_cb)
        form.addRow("Check-In Date:", self.check_in_date)
        form.addRow("Check-Out Date:", self.check_out_date)
        form.addRow("Nights:", self.nights)
        form.addRow("Room Type:", self.room_type)
        form.addRow("Num Rooms:", self.num_rooms)
        form.addRow("Status:", self.status)
        layout.addWidget(details_group)
        
        # Financials Group
        fin_group = QGroupBox("Financials")
        fin_group.setMaximumWidth(600)
        fin_form = QFormLayout(fin_group)
        fin_form.setSpacing(15)
        
        self.cost_rate = QDoubleSpinBox()
        self.cost_rate.setRange(0, 10000000)
        self.cost_rate.setPrefix("PKR ")
        
        self.selling_rate = QDoubleSpinBox()
        self.selling_rate.setRange(0, 10000000)
        self.selling_rate.setPrefix("PKR ")
        
        self.total_lbl = QLabel("PKR 0.00")
        self.total_lbl.setStyleSheet("font-weight: bold; font-size: 14px; color: #3498db;")
        
        fin_form.addRow("Cost Rate (Buying per night) *:", self.cost_rate)
        fin_form.addRow("Selling Rate (per night/room) *:", self.selling_rate)
        fin_form.addRow("Total Price:", self.total_lbl)
        
        layout.addWidget(fin_group)
        
        # Signals for Auto-calculation
        self.nights.valueChanged.connect(self._calculate_total)
        self.num_rooms.valueChanged.connect(self._calculate_total)
        self.selling_rate.valueChanged.connect(self._calculate_total)
        self.check_out_date.dateChanged.connect(self._on_dates_changed)
        self.check_in_date.dateChanged.connect(self._on_dates_changed)
        
        # Buttons
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
        
        layout.addLayout(btn_layout)
        
    def _on_dates_changed(self):
        # Auto update nights based on dates
        days = self.check_in_date.date().daysTo(self.check_out_date.date())
        if days > 0:
            self.nights.blockSignals(True)
            self.nights.setValue(days)
            self.nights.blockSignals(False)
            self._calculate_total()
            
    def _calculate_total(self):
        rooms = self.num_rooms.value()
        nights = self.nights.value()
        rate = self.selling_rate.value()
        
        total = rooms * nights * rate
        self.total_lbl.setText(format_currency(total))
        
    def _on_data_loaded(self, result):
        self.customer_cb.search_input.clear()
        self.hotel_cb.search_input.clear()
        
        customers = result.get('customers', [])
        hotels = result.get('hotels', [])
        
        self.customer_map = {c.full_name: c.id for c in customers}
        if self.customer_map:
            self.customer_cb.set_data([(c.full_name, c.id) for c in customers])
            self.customer_cb.setEnabled(True)
        else:
            self.customer_cb.search_input.setText("No customers found")
            
        self.hotel_map = {h.hotel_name: h.id for h in hotels}
        if self.hotel_map:
            self.hotel_cb.set_data([(h.hotel_name, h.id) for h in hotels])
            self.hotel_cb.setEnabled(True)
        else:
            self.hotel_cb.search_input.setText("No hotels found")
            
        if self.booking:
            if self.booking.customer:
                self.customer_cb.search_input.setText(self.booking.customer.full_name)
            if self.booking.hotel:
                self.hotel_cb.search_input.setText(self.booking.hotel.hotel_name)
            self.check_in_date.setDate(self.booking.check_in_date)
            self.check_out_date.setDate(self.booking.check_out_date)
            self.nights.setValue(self.booking.nights)
            self.room_type.setCurrentText(self.booking.room_type or "Double")
            self.num_rooms.setValue(self.booking.num_rooms)
            self.selling_rate.setValue(float(self.booking.selling_rate or 0))
            self.status.setCurrentText(self.booking.status)
            self._calculate_total()
        
    def _save(self):
        c_name = self.customer_cb.search_input.text()
        h_name = self.hotel_cb.search_input.text()
        
        if not c_name or not h_name or not self.customer_cb.isEnabled():
            QMessageBox.warning(self, "Validation Error", "Customer and Hotel must be selected.")
            return
            
        if self.selling_rate.value() <= 0:
            QMessageBox.warning(self, "Validation Error", "Selling rate must be greater than 0.")
            return
            
        # Calculate total internally as well
        total = self.num_rooms.value() * self.nights.value() * self.selling_rate.value()
            
        data = {
            "id": self.booking.id if self.booking else None,
            "hotel_id": self.hotel_map.get(h_name, ""),
            "customer_id": self.customer_map.get(c_name, ""),
            "check_in_date": self.check_in_date.date().toPython(),
            "check_out_date": self.check_out_date.date().toPython(),
            "nights": self.nights.value(),
            "room_type": self.room_type.currentText(),
            "num_rooms": self.num_rooms.value(),
            "selling_rate": self.selling_rate.value(),
            "total_selling": total,
            "status": self.status.currentText()
        }
        self.viewmodel.save_booking(data, self.current_user_id)
        
    def _on_saved(self, result):
        try:
            from services.accounting_service import AccountingService
            from config.database import get_session
            from models.hotel import HotelBooking
            from models.booking import Booking
            
            with get_session() as session:
                hotel_b = session.query(HotelBooking).get(result.id)
                if hotel_b:
                    # Calculate totals
                    total_cost = self.num_rooms.value() * self.nights.value() * self.cost_rate.value()
                    total_selling = self.num_rooms.value() * self.nights.value() * self.selling_rate.value()
                    
                    central = Booking(
                        booking_type='Hotel_Only',
                        customer_id=hotel_b.customer_id,
                        cost_price=total_cost,
                        selling_price=total_selling,
                        details=f"Hotel Booking - Rooms: {hotel_b.num_rooms}, Nights: {hotel_b.nights}"
                    )
                    session.add(central)
                    session.commit()
                    
                    if total_selling > 0:
                        hotel_name = hotel_b.hotel.hotel_name if hotel_b.hotel else ''
                        invoice = AccountingService().post_standalone_booking(
                            customer_id=hotel_b.customer_id,
                            total_amount=total_selling,
                            item_description=f"Hotel Booking - {hotel_name} - Rooms: {hotel_b.num_rooms}, Nights: {hotel_b.nights}",
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
                        customer_name = hotel_b.customer.full_name if hotel_b.customer else "Unknown Customer"
                        customer_passport = hotel_b.customer.passport_number if hotel_b.customer else ""
                        
                        v_data = {
                            'voucher_no': f"HV-{str(hotel_b.id)[:6].upper()}",
                            'issue_date': datetime.datetime.now().strftime("%d/%m/%Y"),
                            'pkg_category': 'HOTEL ONLY',
                            'print_dt': datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                            'branch_office': 'MAIN OFFICE',
                            'passengers': [
                                {'name': customer_name, 'passport': customer_passport, 'group': ''}
                            ],
                            'accommodation': [
                                {
                                    'city': hotel_b.hotel.city if hotel_b.hotel else '',
                                    'hn': '1',
                                    'hotel_name': hotel_name,
                                    'room': hotel_b.num_rooms,
                                    'room_type': hotel_b.room_type,
                                    'check_in': hotel_b.check_in_date.strftime("%d/%m/%Y") if hasattr(hotel_b.check_in_date, 'strftime') else str(hotel_b.check_in_date),
                                    'check_out': hotel_b.check_out_date.strftime("%d/%m/%Y") if hasattr(hotel_b.check_out_date, 'strftime') else str(hotel_b.check_out_date),
                                    'nights': hotel_b.nights
                                }
                            ],
                            'transport': [],
                            'flights': []
                        }
                        
                        filename = f"Hotel_Voucher_{str(hotel_b.id)[:8]}.pdf"
                        voucher_path = VoucherBuilder(v_data, filename=filename).generate()
                        if hasattr(os, 'startfile'):
                            os.startfile(voucher_path)
                            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save centralized booking or generate invoice/voucher: {str(e)}")
        self.accept()
