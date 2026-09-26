from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QLineEdit, QComboBox, QGroupBox, 
                               QDateEdit, QScrollArea, QWidget, QStackedWidget,
                               QFormLayout, QCheckBox, QMessageBox, QFrame, QSpinBox, QDoubleSpinBox)
from PySide6.QtCore import QDate
from utils.formatters import format_currency

class UmrahBookingPipeline(QDialog):
    def __init__(self, viewmodel, current_user_id, template=None, parent=None):
        super().__init__(parent)
        self.viewmodel = viewmodel
        self.current_user_id = current_user_id
        self.template = template
        self.setWindowTitle("Umrah Booking Pipeline")
        self.setMinimumSize(950, 800)
        
        # Viewmodel Connections
        self.viewmodel.form_data_loaded.connect(self._on_form_data_loaded)
        self.viewmodel.booking_saved.connect(self._on_saved)

        self._apply_styles()
        
        # Load customers
        self.viewmodel.load_form_data()
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.stacked_widget = QStackedWidget()
        
        # Initialize Screens
        self._init_screen_1_builder()
        self._init_screen_2_checkout()
        
        self.stacked_widget.addWidget(self.screen1)
        self.stacked_widget.addWidget(self.screen2)
        
        self.main_layout.addWidget(self.stacked_widget)
        
        # Business Logic: If template is passed, prepopulate and jump to Screen 2
        if self.template:
            self._load_template_data()
            self._calculate_screen1_totals()
            self.stacked_widget.setCurrentIndex(1)
            
    def _apply_styles(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #0D0F1A;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #818CF8;
                border: 1px solid #1E2235;
                border-radius: 8px;
                margin-top: 24px;
                padding-top: 14px;
                background-color: #13152A;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 15px;
                padding: 0 5px;
                color: #818CF8;
            }
            QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {
                background-color: #1A1D2E;
                color: #E2E8F0;
                border: 1.5px solid #2A2D3E;
                border-radius: 6px;
                padding: 0 10px;
                min-height: 35px;
                font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border-color: #4F46E5;
                background-color: #1E2135;
            }
            QLabel {
                font-size: 13px;
                color: #C4CDE8;
            }
            QPushButton {
                background-color: #1A1D2E;
                color: #C4CDE8;
                border-radius: 6px;
                padding: 0 20px;
                font-weight: bold;
                border: 1px solid #2A2D3E;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #252836;
            }
            QPushButton#btn_primary {
                background-color: #4F46E5;
                color: white;
                border: none;
            }
            QPushButton#btn_primary:hover {
                background-color: #4338CA;
            }
            QPushButton#btn_secondary {
                background-color: transparent;
                border: 1.5px solid #4F46E5;
                color: #818CF8;
            }
            QPushButton#btn_secondary:hover {
                background-color: rgba(79, 70, 229, 0.1);
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
        """)

    def _init_screen_1_builder(self):
        self.screen1 = QWidget()
        layout1 = QVBoxLayout(self.screen1)
        layout1.setContentsMargins(0, 0, 0, 0)
        
        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(24, 24, 24, 24)
        c_layout.setSpacing(20)
        
        # Top Header Details
        g_base = QGroupBox("Base Booking Details")
        l_base = QFormLayout(g_base)
        l_base.setContentsMargins(15, 20, 15, 15)
        l_base.setSpacing(12)
        
        self.s1_customer = QComboBox()
        self.s1_customer.addItem("Select Customer...", None)
        # Will be populated by form_data_loaded
        self.s1_date = QDateEdit(QDate.currentDate())
        self.s1_date.setCalendarPopup(True)
        
        l_base.addRow("Customer *:", self.s1_customer)
        l_base.addRow("Departure Date *:", self.s1_date)
        c_layout.addWidget(g_base)
        
        # 1. Flights
        g_flight = QGroupBox("Flights (Return Ticket)")
        l_flight = QFormLayout(g_flight)
        l_flight.setContentsMargins(15, 20, 15, 15)
        l_flight.setSpacing(12)
        
        self.s1_flight_route = QLineEdit(placeholderText="e.g. LHE - JED - LHE")
        self.s1_flight_pnr = QLineEdit(placeholderText="PNR")
        self.s1_flight_airline = QComboBox()
        self.s1_flight_airline.addItems(["Saudi Airlines", "PIA", "Emirates", "Qatar Airways", "Airblue"])
        self.s1_flight_fare = QDoubleSpinBox()
        self.s1_flight_fare.setRange(0, 10000000)
        self.s1_flight_fare.setPrefix("PKR ")
        
        l_flight.addRow("Route:", self.s1_flight_route)
        l_flight.addRow("Airline:", self.s1_flight_airline)
        l_flight.addRow("PNR:", self.s1_flight_pnr)
        l_flight.addRow("Airfare Price:", self.s1_flight_fare)
        c_layout.addWidget(g_flight)
        
        # 2. Visa Processing
        g_visa = QGroupBox("Visa Processing")
        l_visa = QFormLayout(g_visa)
        l_visa.setContentsMargins(15, 20, 15, 15)
        
        self.s1_visa_type = QComboBox()
        self.s1_visa_type.addItems(["Umrah Visa", "Tourist Visa", "Transit Visa"])
        self.s1_visa_fee = QDoubleSpinBox()
        self.s1_visa_fee.setRange(0, 10000000)
        self.s1_visa_fee.setPrefix("PKR ")
        
        l_visa.addRow("Visa Type:", self.s1_visa_type)
        l_visa.addRow("Visa Fee:", self.s1_visa_fee)
        c_layout.addWidget(g_visa)
        
        # 3. Hotels
        g_hotel = QGroupBox("Accommodation")
        l_hotel = QFormLayout(g_hotel)
        l_hotel.setContentsMargins(15, 20, 15, 15)
        
        self.s1_makkah_hotel = QLineEdit(placeholderText="Makkah Hotel Name")
        self.s1_makkah_nights = QSpinBox()
        self.s1_makkah_nights.setRange(0, 90)
        
        self.s1_medinah_hotel = QLineEdit(placeholderText="Medinah Hotel Name")
        self.s1_medinah_nights = QSpinBox()
        self.s1_medinah_nights.setRange(0, 90)
        
        self.s1_room_type = QComboBox()
        self.s1_room_type.addItems(["Double Sharing", "Triple Sharing", "Quad Sharing", "Quint Sharing"])
        
        self.s1_hotel_rate = QDoubleSpinBox()
        self.s1_hotel_rate.setRange(0, 10000000)
        self.s1_hotel_rate.setPrefix("PKR ")
        
        l_hotel.addRow("Makkah Hotel:", self.s1_makkah_hotel)
        l_hotel.addRow("Makkah Nights:", self.s1_makkah_nights)
        l_hotel.addRow("Medinah Hotel:", self.s1_medinah_hotel)
        l_hotel.addRow("Medinah Nights:", self.s1_medinah_nights)
        l_hotel.addRow("Room Type:", self.s1_room_type)
        l_hotel.addRow("Total Hotel Cost:", self.s1_hotel_rate)
        c_layout.addWidget(g_hotel)
        
        # 4. Transport & Ziyarats
        g_trans = QGroupBox("Transport & Ziyarats")
        l_trans = QFormLayout(g_trans)
        l_trans.setContentsMargins(15, 20, 15, 15)
        
        self.s1_transport_type = QComboBox()
        self.s1_transport_type.addItems(["None", "VIP GMC", "Private Car", "Bus / Coaster", "Haramain Train"])
        self.s1_transport_fee = QDoubleSpinBox()
        self.s1_transport_fee.setRange(0, 10000000)
        self.s1_transport_fee.setPrefix("PKR ")
        
        self.s1_ziyarat_makkah = QCheckBox("Include Makkah Ziyarat")
        self.s1_ziyarat_medinah = QCheckBox("Include Medinah Ziyarat")
        self.s1_ziyarat_fee = QDoubleSpinBox()
        self.s1_ziyarat_fee.setRange(0, 10000000)
        self.s1_ziyarat_fee.setPrefix("PKR ")
        
        l_trans.addRow("Transport Type:", self.s1_transport_type)
        l_trans.addRow("Transport Fee:", self.s1_transport_fee)
        l_trans.addRow("", self.s1_ziyarat_makkah)
        l_trans.addRow("", self.s1_ziyarat_medinah)
        l_trans.addRow("Ziyarat Total Fee:", self.s1_ziyarat_fee)
        c_layout.addWidget(g_trans)
        
        # Set Container
        scroll.setWidget(container)
        layout1.addWidget(scroll)
        
        # Sticky Footer
        footer = QFrame()
        footer.setStyleSheet("background-color: #13152A; border-top: 1px solid #1E2235;")
        f_layout = QHBoxLayout(footer)
        f_layout.setContentsMargins(24, 15, 24, 15)
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        
        btn_next = QPushButton("Calculate Total & Generate Invoice →")
        btn_next.setObjectName("btn_primary")
        btn_next.setShortcut("Return")
        btn_next.clicked.connect(self._go_to_checkout)
        
        f_layout.addWidget(btn_cancel)
        f_layout.addStretch()
        f_layout.addWidget(btn_next)
        
        layout1.addWidget(footer)

    def _init_screen_2_checkout(self):
        self.screen2 = QWidget()
        layout2 = QVBoxLayout(self.screen2)
        layout2.setContentsMargins(24, 24, 24, 24)
        layout2.setSpacing(20)
        
        title = QLabel("Billing & Checkout")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #FFFFFF;")
        layout2.addWidget(title)
        
        # Split into left (Summary) and right (Financials)
        h_split = QHBoxLayout()
        h_split.setSpacing(20)
        
        # --- Left: Summary Panel ---
        g_summary = QGroupBox("Booking Summary")
        l_summary = QFormLayout(g_summary)
        l_summary.setContentsMargins(20, 20, 20, 20)
        
        self.s2_lbl_flight = QLabel("0.00")
        self.s2_lbl_visa = QLabel("0.00")
        self.s2_lbl_hotel = QLabel("0.00")
        self.s2_lbl_transport = QLabel("0.00")
        self.s2_lbl_ziyarat = QLabel("0.00")
        self.s2_lbl_subtotal = QLabel("0.00")
        self.s2_lbl_subtotal.setStyleSheet("font-weight: bold; color: #FFFFFF; font-size: 16px;")
        
        l_summary.addRow("Flights Cost:", self.s2_lbl_flight)
        l_summary.addRow("Visa Cost:", self.s2_lbl_visa)
        l_summary.addRow("Hotel Cost:", self.s2_lbl_hotel)
        l_summary.addRow("Transport Cost:", self.s2_lbl_transport)
        l_summary.addRow("Ziyarat Cost:", self.s2_lbl_ziyarat)
        
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("border-top: 1px solid #2A2D3E; margin: 10px 0;")
        l_summary.addRow(divider)
        
        l_summary.addRow("Subtotal:", self.s2_lbl_subtotal)
        h_split.addWidget(g_summary, stretch=1)
        
        # --- Right: Financials ---
        g_fin = QGroupBox("Invoice Generation")
        l_fin = QFormLayout(g_fin)
        l_fin.setContentsMargins(20, 20, 20, 20)
        
        self.s2_service_charges = QDoubleSpinBox()
        self.s2_service_charges.setRange(0, 10000000)
        self.s2_service_charges.setPrefix("PKR ")
        self.s2_service_charges.valueChanged.connect(self._calculate_final_totals)
        
        self.s2_discount = QDoubleSpinBox()
        self.s2_discount.setRange(0, 10000000)
        self.s2_discount.setPrefix("- PKR ")
        self.s2_discount.valueChanged.connect(self._calculate_final_totals)
        
        self.s2_grand_total = QLabel("0.00")
        self.s2_grand_total.setStyleSheet("font-size: 26px; font-weight: bold; color: #4ADE80; min-height: 40px;")
        
        self.s2_amount_paid = QDoubleSpinBox()
        self.s2_amount_paid.setRange(0, 10000000)
        self.s2_amount_paid.setPrefix("PKR ")
        self.s2_amount_paid.valueChanged.connect(self._calculate_final_totals)
        
        self.s2_balance_due = QLabel("0.00")
        self.s2_balance_due.setStyleSheet("font-size: 16px; font-weight: bold; color: #F87171;")
        
        self.s2_payment_method = QComboBox()
        self.s2_payment_method.addItems(["Cash", "Bank Transfer", "Cheque", "Credit Card"])
        
        l_fin.addRow("Service Charges (+):", self.s2_service_charges)
        l_fin.addRow("Discount (-):", self.s2_discount)
        l_fin.addRow(QFrame())
        l_fin.addRow("Grand Total:", self.s2_grand_total)
        l_fin.addRow(QFrame())
        l_fin.addRow("Amount Received:", self.s2_amount_paid)
        l_fin.addRow("Balance Due:", self.s2_balance_due)
        l_fin.addRow("Payment Method:", self.s2_payment_method)
        
        h_split.addWidget(g_fin, stretch=1)
        layout2.addLayout(h_split)
        
        layout2.addStretch()
        
        # Footer
        footer = QFrame()
        f_layout = QHBoxLayout(footer)
        f_layout.setContentsMargins(0, 15, 0, 0)
        
        btn_back = QPushButton("← Back to Edit")
        btn_back.setObjectName("btn_secondary")
        btn_back.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        
        btn_confirm = QPushButton("Confirm Booking & Print Invoice ✓")
        btn_confirm.setObjectName("btn_primary")
        btn_confirm.setShortcut("Return")
        btn_confirm.setMinimumHeight(45)
        btn_confirm.setStyleSheet("font-size: 15px; background-color: #166534;")
        btn_confirm.clicked.connect(self._confirm_booking)
        
        f_layout.addWidget(btn_back)
        f_layout.addStretch()
        f_layout.addWidget(btn_confirm)
        
        layout2.addWidget(footer)
        
    def _calculate_screen1_totals(self):
        f = self.s1_flight_fare.value()
        v = self.s1_visa_fee.value()
        h = self.s1_hotel_rate.value()
        t = self.s1_transport_fee.value()
        z = self.s1_ziyarat_fee.value()
        
        subtotal = f + v + h + t + z
        
        self.s2_lbl_flight.setText(format_currency(f))
        self.s2_lbl_visa.setText(format_currency(v))
        self.s2_lbl_hotel.setText(format_currency(h))
        self.s2_lbl_transport.setText(format_currency(t))
        self.s2_lbl_ziyarat.setText(format_currency(z))
        
        self.s2_lbl_subtotal.setText(format_currency(subtotal))
        
        self.subtotal_value = subtotal
        self._calculate_final_totals()
        
    def _calculate_final_totals(self):
        sc = self.s2_service_charges.value()
        disc = self.s2_discount.value()
        
        grand_total = self.subtotal_value + sc - disc
        if grand_total < 0: grand_total = 0
        
        self.s2_grand_total.setText(format_currency(grand_total))
        
        paid = self.s2_amount_paid.value()
        balance = grand_total - paid
        if balance < 0: balance = 0
        
        self.s2_balance_due.setText(format_currency(balance))

    def _go_to_checkout(self):
        if self.s1_customer.currentIndex() == 0:
            QMessageBox.warning(self, "Validation Error", "Please select a customer.")
            return
            
        self._calculate_screen1_totals()
        self.stacked_widget.setCurrentIndex(1)
        
    def _load_template_data(self):
        # Implementation for loading self.template into UI fields
        pass

    def _on_form_data_loaded(self, result):
        customers = result.get('customers', [])
        self.s1_customer.clear()
        self.s1_customer.addItem("Select Customer...", None)
        for c in customers:
            self.s1_customer.addItem(c.full_name, c.id)

    def _on_saved(self, pdf_path):
        QMessageBox.information(self, "Success", f"Booking and Invoice have been generated successfully!\n\nInvoice PDF: {pdf_path}")
        self.accept()
        
    def _confirm_booking(self):
        # Build JSON dicts
        flight_details = {
            "route": self.s1_flight_route.text(),
            "pnr": self.s1_flight_pnr.text(),
            "airline": self.s1_flight_airline.currentText()
        }
        
        visa_details = {
            "type": self.s1_visa_type.currentText()
        }
        
        hotel_details = {
            "makkah_hotel": self.s1_makkah_hotel.text(),
            "makkah_nights": self.s1_makkah_nights.value(),
            "medinah_hotel": self.s1_medinah_hotel.text(),
            "medinah_nights": self.s1_medinah_nights.value(),
            "room_type": self.s1_room_type.currentText()
        }
        
        transport_details = {
            "type": self.s1_transport_type.currentText()
        }
        
        ziyarat_details = {
            "makkah": self.s1_ziyarat_makkah.isChecked(),
            "medinah": self.s1_ziyarat_medinah.isChecked()
        }
        
        booking_data = {
            "customer_id": self.s1_customer.currentData(),
            "departure_date": self.s1_date.date().toPython(),
            "flight_details": flight_details,
            "visa_details": visa_details,
            "hotel_details": hotel_details,
            "transport_details": transport_details,
            "ziyarat_details": ziyarat_details,
            
            # Financials for CustomUmrahBooking & Invoice
            "base_package_price": self.s1_hotel_rate.value() + self.s1_visa_fee.value() + self.s1_transport_fee.value() + self.s1_ziyarat_fee.value(),
            "airfare_price": self.s1_flight_fare.value(),
            "service_charges": self.s2_service_charges.value(),
            "discount": self.s2_discount.value(),
            "amount_paid": self.s2_amount_paid.value(),
            "payment_method": self.s2_payment_method.currentText(),
            
            "subtotal": getattr(self, 'subtotal_value', 0),
            "grand_total": getattr(self, 'subtotal_value', 0) + self.s2_service_charges.value() - self.s2_discount.value()
        }
        
        # Trigger save (ViewModel will handle DB commit and PDF generation)
        self.viewmodel.save_umrah_booking_and_invoice(booking_data, self.current_user_id)
