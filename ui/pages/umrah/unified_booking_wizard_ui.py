from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QComboBox,
    QLineEdit, QPushButton, QLabel, QFormLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QStackedWidget, QMessageBox, QDateEdit,
    QScrollArea, QDialog, QFrame, QDoubleSpinBox, QAbstractItemView,
    QSpinBox, QGridLayout, QSizePolicy,
)
from PySide6.QtCore import Qt, QDate, QTime
from PySide6.QtGui import QFont
from services.umrah_checkout_service import UmrahCheckoutService
from services.customer_service import CustomerService
from services.invoice_generator import InvoiceGenerator
from config.database import get_session
from models.umrah import CustomUmrahBooking
from models.accounting import Invoice
import os

class ModernCustomerSelector(QWidget):
    """Replaces standard QComboBox for Customer Selection"""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("🔍 Search Customer by Name, Phone, or CNIC...")
        self.search_field.setStyleSheet("padding: 8px; font-size: 14px; border-radius: 5px; border: 1px solid #475569;")

        self.customer_map = {}
        self.id_to_name_map = {}
        layout.addWidget(self.search_field)

    def set_data(self, customers_list):
        self.customer_map = {name: cid for name, cid in customers_list}
        self.id_to_name_map = {cid: name for name, cid in customers_list}
        
        from PySide6.QtWidgets import QCompleter
        from PySide6.QtCore import Qt
        self.completer = QCompleter(list(self.customer_map.keys()))
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        
        dropdown_style = """
            QAbstractItemView {
                background-color: #1E1E2E; color: #FFFFFF;
                selection-background-color: #FF512F;
                border: 1px solid #333344; border-radius: 5px;
            }
        """
        popup = self.completer.popup()
        if popup:
            popup.setStyleSheet(dropdown_style)
            
        self.search_field.setCompleter(self.completer)

    def currentData(self):
        return self.customer_map.get(self.search_field.text())

    def clear(self):
        self.search_field.clear()

    def set_by_id(self, customer_id):
        name = self.id_to_name_map.get(customer_id)
        if name:
            self.search_field.setText(name)


class FlightLegWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("QFrame { background-color: #2D3748; border-radius: 5px; margin-bottom: 5px; }")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        top_layout = QHBoxLayout()
        self.lbl_title = QLabel("✈ Flight Leg")
        self.lbl_title.setStyleSheet("font-weight: bold; font-size: 13pt;")
        btn_delete = QPushButton("✖")
        btn_delete.setObjectName("btn_icon_danger")
        btn_delete.setFixedSize(28, 28)
        btn_delete.clicked.connect(self.deleteLater)
        top_layout.addWidget(self.lbl_title)
        top_layout.addStretch()
        top_layout.addWidget(btn_delete)
        layout.addLayout(top_layout)
        
        form_layout = QFormLayout()
        self.f_leg_type = QComboBox()
        self.f_leg_type.addItems(["Outbound", "Return", "Transit", "Multi-City"])
        self.f_airline = QLineEdit(placeholderText="e.g. Saudi Airlines")
        self.f_flight_number = QLineEdit(placeholderText="Flight No (e.g. PK-831)")
        self.f_origin = QLineEdit(placeholderText="Origin (e.g. KHI)")
        self.f_dest = QLineEdit(placeholderText="Destination (e.g. JED)")
        from PySide6.QtWidgets import QTimeEdit, QDateEdit
        from PySide6.QtCore import QTime, QDate
        self.f_flight_date = QDateEdit(QDate.currentDate())
        self.f_flight_date.setCalendarPopup(True)
        self.f_dep_time = QTimeEdit(QTime.currentTime())
        self.f_arr_time = QTimeEdit(QTime.currentTime().addSecs(3600 * 2))
        self.f_pnr = QLineEdit(placeholderText="PNR (Optional)")
        self.f_pax = QLineEdit("1", placeholderText="Passengers")
        from PySide6.QtWidgets import QDoubleSpinBox
        self.f_purchase_price = QDoubleSpinBox()
        self.f_purchase_price.setMaximum(100000000)
        self.f_purchase_price.setPrefix("Cost: ")
        
        self.f_sales_price = QDoubleSpinBox()
        self.f_sales_price.setMaximum(100000000)
        self.f_sales_price.setPrefix("Sell: ")
        
        self.f_profit = QLineEdit("0")
        self.f_profit.setReadOnly(True)
        self.f_profit.setPlaceholderText("Profit")
        
        self.f_purchase_price.valueChanged.connect(self.calculate_profit)
        self.f_sales_price.valueChanged.connect(self.calculate_profit)
        
        form_layout.addRow("Leg Type:", self.f_leg_type)
        form_layout.addRow("Airline:", self.f_airline)
        form_layout.addRow("Flight No:", self.f_flight_number)
        form_layout.addRow("Route:", self.f_origin)
        form_layout.addRow("To:", self.f_dest)
        form_layout.addRow("Flight Date:", self.f_flight_date)
        form_layout.addRow("Dep Time:", self.f_dep_time)
        form_layout.addRow("Arr Time:", self.f_arr_time)
        form_layout.addRow("PNR:", self.f_pnr)
        form_layout.addRow("Passengers:", self.f_pax)
        form_layout.addRow("Purchase Price:", self.f_purchase_price)
        form_layout.addRow("Sales Price:", self.f_sales_price)
        form_layout.addRow("Calculated Profit:", self.f_profit)
        
        layout.addLayout(form_layout)
        
    def calculate_profit(self):
        purchase = self.f_purchase_price.value()
        sales = self.f_sales_price.value()
        self.f_profit.setText(str(sales - purchase))
        
    def get_data(self):
        return {
            'leg_type': self.f_leg_type.currentText(),
            'airline': self.f_airline.text(),
            'flight_number': self.f_flight_number.text(),
            'origin': self.f_origin.text(),
            'destination': self.f_dest.text(),
            'departure_date': self.f_flight_date.date().toPython(),
            'departure_time': self.f_dep_time.time().toString("HH:mm"),
            'arrival_time': self.f_arr_time.time().toString("HH:mm"),
            'pnr': self.f_pnr.text(),
            'pax': int(self.f_pax.text() or 1),
            'purchase_price': self.f_purchase_price.value(),
            'sales_price': self.f_sales_price.value(),
            'profit': float(self.f_profit.text() or 0)
        }

class HotelStayWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("QFrame { background-color: #2D3748; border-radius: 5px; margin-bottom: 5px; }")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        top_layout = QHBoxLayout()
        self.lbl_title = QLabel("🏨 Hotel Stay")
        self.lbl_title.setStyleSheet("font-weight: bold; font-size: 13pt;")
        btn_delete = QPushButton("✖")
        btn_delete.setObjectName("btn_icon_danger")
        btn_delete.setFixedSize(28, 28)
        btn_delete.clicked.connect(self.deleteLater)
        top_layout.addWidget(self.lbl_title)
        top_layout.addStretch()
        top_layout.addWidget(btn_delete)
        layout.addLayout(top_layout)
        
        form_layout = QFormLayout()
        self.h_city = QComboBox()
        self.h_city.addItems(["Makkah", "Medinah", "Jeddah", "Taif", "Dubai", "Other"])
        self.h_city.setEditable(True)
        
        from ui.components.searchable_combo_box import SearchableComboBox
        self.h_name = SearchableComboBox()
        self.h_name.search_input.setPlaceholderText("Hotel Name")
        
        self.h_name.item_selected.connect(self._on_hotel_selected)
        
        self.h_city.currentTextChanged.connect(self.load_hotels_for_city)
        
        self.h_hn_number = QLineEdit(placeholderText="HN Number")
        self.h_reservation_name = QLineEdit(placeholderText="Reservation Name")
        self.h_room_type = QComboBox()
        self.h_room_type.addItems(["SINGLE", "DOUBLE", "TRIPLE", "QUAD", "QUINT", "SHARING"])
        self.h_rooms_count = QLineEdit("1", placeholderText="No. of Rooms")
        
        from PySide6.QtWidgets import QTimeEdit, QSpinBox
        from PySide6.QtCore import QTime
        self.h_checkin = QDateEdit(QDate.currentDate())
        self.h_checkin.setCalendarPopup(True)
        self.h_checkin_time = QTimeEdit(QTime(16, 0))
        
        self.h_checkout = QDateEdit(QDate.currentDate().addDays(7))
        self.h_checkout.setCalendarPopup(True)
        self.h_checkout_time = QTimeEdit(QTime(12, 0))
        
        self.h_nights = QSpinBox()
        self.h_nights.setMinimum(1)
        self.h_nights.setMaximum(90)
        self.h_nights.setValue(7)
        
        from PySide6.QtWidgets import QDoubleSpinBox
        self.h_purchase_price = QDoubleSpinBox()
        self.h_purchase_price.setMaximum(100000000)
        self.h_purchase_price.setPrefix("Cost: ")
        
        self.h_sales_price = QDoubleSpinBox()
        self.h_sales_price.setMaximum(100000000)
        self.h_sales_price.setPrefix("Sell: ")
        
        self.h_profit = QLineEdit("0")
        self.h_profit.setReadOnly(True)
        self.h_profit.setPlaceholderText("Profit")
        
        self.h_purchase_price.valueChanged.connect(self.calculate_profit)
        self.h_sales_price.valueChanged.connect(self.calculate_profit)
        
        form_layout.addRow("City:", self.h_city)
        form_layout.addRow("Hotel Name:", self.h_name)
        form_layout.addRow("HN Number:", self.h_hn_number)
        form_layout.addRow("Reservation Name:", self.h_reservation_name)
        form_layout.addRow("Room Type:", self.h_room_type)
        form_layout.addRow("Rooms Count:", self.h_rooms_count)
        form_layout.addRow("Check-In Date:", self.h_checkin)
        form_layout.addRow("Check-In Time:", self.h_checkin_time)
        form_layout.addRow("Check-Out Date:", self.h_checkout)
        form_layout.addRow("Check-Out Time:", self.h_checkout_time)
        form_layout.addRow("Nights:", self.h_nights)
        form_layout.addRow("Purchase Price:", self.h_purchase_price)
        form_layout.addRow("Sales Price:", self.h_sales_price)
        form_layout.addRow("Calculated Profit:", self.h_profit)
        
        layout.addLayout(form_layout)
        
        # Load initially
        self.load_hotels_for_city(self.h_city.currentText())

    def _on_hotel_selected(self, hotel_id: str):
        from config.database import get_session
        from models.hotel import Hotel
        try:
            with get_session() as session:
                hotel = session.get(Hotel, hotel_id)
                if hotel and hotel.hotel_code:
                    self.h_hn_number.setText(hotel.hotel_code)
        except Exception as e:
            print(f"Error fetching hotel details: {e}")

    def load_hotels_for_city(self, city_name):
        from config.database import get_session
        from models.hotel import Hotel
        try:
            with get_session() as session:
                hotels = session.query(Hotel).filter(Hotel.city.ilike(f"%{city_name}%")).all()
                data_list = [(h.hotel_name, h.id) for h in hotels]
                self.h_name.set_data(data_list)
        except Exception as e:
            print(f"Error loading hotels for city {city_name}: {e}")

    def calculate_profit(self):
        purchase = self.h_purchase_price.value()
        sales = self.h_sales_price.value()
        self.h_profit.setText(str(sales - purchase))
        
    def get_data(self):
        return {
            'city': self.h_city.currentText(),
            'hotel_name': self.h_name.search_input.text(),
            'hn_number': self.h_hn_number.text(),
            'reservation_name': self.h_reservation_name.text(),
            'room_type': self.h_room_type.currentText(),
            'rooms_count': int(self.h_rooms_count.text() or 1),
            'check_in_date': self.h_checkin.date().toPython(),
            'check_in_time': self.h_checkin_time.time().toString("HH:mm"),
            'check_out_date': self.h_checkout.date().toPython(),
            'check_out_time': self.h_checkout_time.time().toString("HH:mm"),
            'nights': self.h_nights.value(),
            'purchase_price': self.h_purchase_price.value(),
            'sales_price': self.h_sales_price.value(),
            'profit': float(self.h_profit.text() or 0)
        }

class TransportWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("QFrame { background-color: #2D3748; border-radius: 5px; margin-bottom: 5px; }")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        top_layout = QHBoxLayout()
        self.lbl_title = QLabel("🚌 Transport")
        self.lbl_title.setStyleSheet("font-weight: bold; font-size: 13pt;")
        btn_delete = QPushButton("✖")
        btn_delete.setObjectName("btn_icon_danger")
        btn_delete.setFixedSize(28, 28)
        btn_delete.clicked.connect(self.deleteLater)
        top_layout.addWidget(self.lbl_title)
        top_layout.addStretch()
        top_layout.addWidget(btn_delete)
        layout.addLayout(top_layout)
        
        form_layout = QFormLayout()
        
        self.t_type = QComboBox()
        self.t_type.addItems(["BUS", "GMC", "CAR", "HIACE", "SUV"])
        self.t_type.setEditable(True)
        self.t_tn_number = QLineEdit(placeholderText="TN Number")
        self.t_route = QLineEdit(placeholderText="Route (e.g. JED-MAK)")
        self.t_contact = QLineEdit(placeholderText="Contact Person")
        self.t_booking_ref = QLineEdit(placeholderText="Booking Ref")
        self.t_pickup_date = QDateEdit(QDate.currentDate())
        self.t_pickup_date.setCalendarPopup(True)
        self.t_purchase_price = QDoubleSpinBox()
        self.t_purchase_price.setMaximum(100000000)
        self.t_purchase_price.setPrefix("Cost: ")
        
        self.t_sales_price = QDoubleSpinBox()
        self.t_sales_price.setMaximum(100000000)
        self.t_sales_price.setPrefix("Sell: ")
        
        self.t_profit = QLineEdit("0")
        self.t_profit.setReadOnly(True)
        self.t_profit.setPlaceholderText("Profit")
        
        self.t_purchase_price.valueChanged.connect(self.calculate_transport_profit)
        self.t_sales_price.valueChanged.connect(self.calculate_transport_profit)
        
        form_layout.addRow("Vehicle Type:", self.t_type)
        form_layout.addRow("TN Number:", self.t_tn_number)
        form_layout.addRow("Service Route:", self.t_route)
        form_layout.addRow("Contact:", self.t_contact)
        form_layout.addRow("Booking Ref:", self.t_booking_ref)
        form_layout.addRow("Pickup Date:", self.t_pickup_date)
        form_layout.addRow("Purchase Price:", self.t_purchase_price)
        form_layout.addRow("Sales Price:", self.t_sales_price)
        form_layout.addRow("Calculated Profit:", self.t_profit)
        
        layout.addLayout(form_layout)
        
    def calculate_transport_profit(self):
        profit = self.t_sales_price.value() - self.t_purchase_price.value()
        self.t_profit.setText(str(round(profit, 2)))
        
    def get_data(self):
        if not self.t_type.currentText().strip():
            return None
        return {
            'type': self.t_type.currentText(),
            'tn_number': self.t_tn_number.text(),
            'service_route': self.t_route.text(),
            'contact_person': self.t_contact.text(),
            'booking_ref': self.t_booking_ref.text(),
            'pickup_date': self.t_pickup_date.date().toString("yyyy-MM-dd"),
            'purchase_price': self.t_purchase_price.value(),
            'sales_price': self.t_sales_price.value()
        }
        
    def load_data(self, data):
        if not data: return
        self.t_type.setCurrentText(data.get('type', 'BUS'))
        self.t_tn_number.setText(data.get('tn_number', ''))
        self.t_route.setText(data.get('service_route', ''))
        self.t_contact.setText(data.get('contact_person', ''))
        self.t_booking_ref.setText(data.get('booking_ref', ''))
        
        pd = data.get('pickup_date')
        if pd:
            if isinstance(pd, str):
                self.t_pickup_date.setDate(QDate.fromString(pd, "yyyy-MM-dd" if "-" in pd else Qt.DateFormat.ISODate))
            else:
                self.t_pickup_date.setDate(pd)
                
        self.t_purchase_price.setValue(float(data.get('purchase_price', 0.0)))
        self.t_sales_price.setValue(float(data.get('sales_price', 0.0)))

class UnifiedBookingWizardUI(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Unified Umrah Booking Wizard")
        self.setMinimumSize(1000, 750)
        self.checkout_service = UmrahCheckoutService()
        self.customer_service = CustomerService()
        
        self.current_booking_id = None
        self.is_edit_mode = False
        
        self.pax_names_list = []
        self.pax_passport_map = {}
        
        self.setup_ui()
        
        # Initial Calculations
        self.calculate_base_profit()
        self.calculate_visa_profit()
        
        self.load_customers()
        self.load_templates()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        self.stacked_widget = QStackedWidget()
        
        # --- SCREEN 1: THE BUILDER ---
        self.builder_widget = QWidget()
        builder_layout = QVBoxLayout(self.builder_widget)
        
        # Master Template Selection
        template_layout = QHBoxLayout()
        self.cb_template = QComboBox()
        self.cb_template.setMinimumHeight(40)
        self.cb_template.addItem("Load from Master Template...", None)
        self.cb_template.currentIndexChanged.connect(self._apply_template_data)
        template_layout.addWidget(QLabel("<b>Template:</b>"))
        template_layout.addWidget(self.cb_template, 1)
        builder_layout.addLayout(template_layout)

        # Top: Customer Selection
        customer_layout = QHBoxLayout()
        self.cb_customer = ModernCustomerSelector()
        self.cb_customer.setMinimumHeight(40)
        
        btn_new_customer = QPushButton("+ New Customer")
        btn_new_customer.setObjectName("btn_secondary")
        btn_new_customer.setMinimumHeight(40)
        
        customer_layout.addWidget(QLabel("<b>Customer:</b>"))
        customer_layout.addWidget(self.cb_customer, 1)
        customer_layout.addWidget(btn_new_customer)
        btn_new_customer.clicked.connect(self.open_new_customer_form)
        builder_layout.addLayout(customer_layout)
        
        # Scroll Area for Modules
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        modules_widget = QWidget()
        self.modules_layout = QVBoxLayout(modules_widget)
        self.modules_layout.setSpacing(15)
        
        # 0.1 Voucher Metadata
        group_voucher = QGroupBox("📄 Voucher Metadata")
        voucher_layout = QFormLayout(group_voucher)
        self.v_voucher_no = QLineEdit()
        self.v_voucher_no.setPlaceholderText("Auto-generated (e.g. HV-12345)")
        self.v_issue_date = QDateEdit(QDate.currentDate())
        self.v_issue_date.setCalendarPopup(True)
        self.v_pkg_category = QComboBox()
        self.v_pkg_category.addItems(["CUSTOM UMRAH", "EXECUTIVE", "STANDARD", "ECONOMY"])
        self.v_pkg_category.setEditable(True)
        
        voucher_layout.addRow("Voucher No:", self.v_voucher_no)
        voucher_layout.addRow("Issue Date:", self.v_issue_date)
        voucher_layout.addRow("Package Category:", self.v_pkg_category)
        self.modules_layout.addWidget(group_voucher)

        # 0.5 Base Package Price — Categorical Pricing Matrix
        group_base = QGroupBox("💼 Base Package — Pricing Matrix")
        group_base_layout = QVBoxLayout(group_base)
        group_base_layout.setSpacing(8)

        # ── Column header row ──────────────────────────────────────────
        header_grid = QGridLayout()
        header_grid.setColumnStretch(0, 2)   # label column
        header_grid.setColumnStretch(1, 1)   # qty
        header_grid.setColumnStretch(2, 2)   # cost
        header_grid.setColumnStretch(3, 2)   # sell

        _bold = QFont()
        _bold.setBold(True)

        def _hdr(text):
            lbl = QLabel(text)
            lbl.setFont(_bold)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #94A3B8; font-size: 9pt;")
            return lbl

        header_grid.addWidget(_hdr("TYPE"),         0, 0)
        header_grid.addWidget(_hdr("QTY"),          0, 1)
        header_grid.addWidget(_hdr("COST / PAX"),   0, 2)
        header_grid.addWidget(_hdr("SELL / PAX"),   0, 3)
        group_base_layout.addLayout(header_grid)

        # ── Divider ────────────────────────────────────────────────────
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: #334155;")
        group_base_layout.addWidget(divider)

        # ── Matrix grid — 3 data rows ──────────────────────────────────
        matrix_grid = QGridLayout()
        matrix_grid.setColumnStretch(0, 2)
        matrix_grid.setColumnStretch(1, 1)
        matrix_grid.setColumnStretch(2, 2)
        matrix_grid.setColumnStretch(3, 2)
        matrix_grid.setVerticalSpacing(8)

        _ROW_STYLES = {
            "Adult":  "color: #60A5FA;",   # blue
            "Child":  "color: #34D399;",   # green
            "Infant": "color: #FBBF24;",   # amber
        }
        _ROW_ICONS = {"Adult": "🧑 Adult", "Child": "👦 Child", "Infant": "👶 Infant"}

        def _price_edit(placeholder="0"):
            le = QLineEdit(placeholder)
            le.setAlignment(Qt.AlignmentFlag.AlignRight)
            le.setStyleSheet("padding: 4px 6px; font-size: 10pt;")
            le.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            return le

        def _qty_spin():
            sb = QSpinBox()
            sb.setRange(0, 999)
            sb.setValue(0)
            sb.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sb.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            return sb

        # ── Adult row (row index 0) ─────────────────────────────────────
        lbl_adult = QLabel(_ROW_ICONS["Adult"])
        lbl_adult.setStyleSheet(_ROW_STYLES["Adult"] + " font-weight: bold;")
        self.spin_adult_qty   = _qty_spin()
        self.t_adult_cost     = _price_edit("0")
        self.t_adult_sell     = _price_edit("0")
        self.spin_adult_qty.setValue(1)   # sensible default

        matrix_grid.addWidget(lbl_adult,            0, 0)
        matrix_grid.addWidget(self.spin_adult_qty,  0, 1)
        matrix_grid.addWidget(self.t_adult_cost,    0, 2)
        matrix_grid.addWidget(self.t_adult_sell,    0, 3)

        # ── Child row (row index 1) ─────────────────────────────────────
        lbl_child = QLabel(_ROW_ICONS["Child"])
        lbl_child.setStyleSheet(_ROW_STYLES["Child"] + " font-weight: bold;")
        self.spin_child_qty   = _qty_spin()
        self.t_child_cost     = _price_edit("0")
        self.t_child_sell     = _price_edit("0")

        matrix_grid.addWidget(lbl_child,            1, 0)
        matrix_grid.addWidget(self.spin_child_qty,  1, 1)
        matrix_grid.addWidget(self.t_child_cost,    1, 2)
        matrix_grid.addWidget(self.t_child_sell,    1, 3)

        # ── Infant row (row index 2) ────────────────────────────────────
        lbl_infant = QLabel(_ROW_ICONS["Infant"])
        lbl_infant.setStyleSheet(_ROW_STYLES["Infant"] + " font-weight: bold;")
        self.spin_infant_qty  = _qty_spin()
        self.t_infant_cost    = _price_edit("0")
        self.t_infant_sell    = _price_edit("0")

        matrix_grid.addWidget(lbl_infant,           2, 0)
        matrix_grid.addWidget(self.spin_infant_qty, 2, 1)
        matrix_grid.addWidget(self.t_infant_cost,   2, 2)
        matrix_grid.addWidget(self.t_infant_sell,   2, 3)

        group_base_layout.addLayout(matrix_grid)

        # ── Second divider ─────────────────────────────────────────────
        divider2 = QFrame()
        divider2.setFrameShape(QFrame.Shape.HLine)
        divider2.setStyleSheet("color: #334155;")
        group_base_layout.addWidget(divider2)

        # ── Live totals row ────────────────────────────────────────────
        totals_layout = QHBoxLayout()
        totals_layout.setSpacing(20)

        self.lbl_live_grand_total = QLabel("Grand Total:  PKR 0.00")
        self.lbl_live_grand_total.setStyleSheet(
            "font-size: 13pt; font-weight: bold; color: #48BB78;"
        )

        self.lbl_live_net_profit = QLabel("Net Profit:  PKR 0.00")
        self.lbl_live_net_profit.setStyleSheet(
            "font-size: 13pt; font-weight: bold; color: #F6AD55;"
        )

        totals_layout.addStretch()
        totals_layout.addWidget(self.lbl_live_grand_total)
        totals_layout.addWidget(self.lbl_live_net_profit)
        group_base_layout.addLayout(totals_layout)

        self.modules_layout.addWidget(group_base)

        # ── Wire all matrix signals → live recalculator ────────────────
        for spin in (self.spin_adult_qty, self.spin_child_qty, self.spin_infant_qty):
            spin.valueChanged.connect(self.calculate_base_profit)
            spin.valueChanged.connect(self.sync_pax_from_matrix)   # Phase 3
        for field in (
            self.t_adult_cost,  self.t_adult_sell,
            self.t_child_cost,  self.t_child_sell,
            self.t_infant_cost, self.t_infant_sell,
        ):
            field.textChanged.connect(self.calculate_base_profit)


        # 0.5 Passengers Roster
        group_pax = QGroupBox("👥 Passengers")
        pax_layout = QVBoxLayout(group_pax)
        
        self.pax_scroll = QScrollArea()
        self.pax_scroll.setWidgetResizable(True)
        self.pax_scroll.setMinimumHeight(150)
        self.pax_scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollArea > QWidget > QWidget { background: transparent; }
        """)
        
        self.pax_container = QWidget()
        self.pax_container_layout = QVBoxLayout(self.pax_container)
        self.pax_container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.pax_container_layout.setContentsMargins(0, 0, 0, 0)
        self.pax_scroll.setWidget(self.pax_container)
        
        self.pax_widgets = []
        
        pax_btn_layout = QHBoxLayout()
        btn_add_pax = QPushButton("+ Add Passenger")
        btn_add_pax.clicked.connect(lambda: self.add_pax_row())
        
        self.cb_group_leader = QComboBox()
        self.cb_group_leader.addItem("Select Group Leader...")
        self.cb_group_leader.currentTextChanged.connect(self._on_group_leader_selected)
        
        btn_remove_pax = QPushButton("- Remove Passenger")
        btn_remove_pax.clicked.connect(self.remove_pax_row)
        
        pax_btn_layout.addWidget(btn_add_pax)
        pax_btn_layout.addWidget(QLabel("Group Leader:"))
        pax_btn_layout.addWidget(self.cb_group_leader, 1)
        pax_btn_layout.addWidget(btn_remove_pax)
        
        pax_layout.addWidget(self.pax_scroll)
        pax_layout.addLayout(pax_btn_layout)
        self.modules_layout.addWidget(group_pax)

        # 1. Flights Section
        self.flights_wrapper = QWidget()
        self.flights_container = QVBoxLayout(self.flights_wrapper)
        self.flights_container.setContentsMargins(0,0,0,0)
        btn_add_flight = QPushButton("+ Add Flight Leg")
        btn_add_flight.setObjectName("btn_secondary")
        btn_add_flight.clicked.connect(self.add_flight_widget)
        self.modules_layout.addWidget(QLabel("<b>Flights</b>"))
        self.modules_layout.addWidget(self.flights_wrapper)
        self.modules_layout.addWidget(btn_add_flight)
        
        # 2. Visa Section
        self.group_visa = QFrame()
        self.group_visa.setFrameShape(QFrame.Shape.StyledPanel)
        self.group_visa.setStyleSheet("QFrame { background-color: #2D3748; border-radius: 5px; margin-bottom: 5px; }")
        
        v_main_layout = QVBoxLayout(self.group_visa)
        
        v_top = QHBoxLayout()
        v_title = QLabel("🛂 Visa Applications")
        v_title.setStyleSheet("font-weight: bold; font-size: 13pt;")
        self.btn_toggle_visa = QPushButton("✖ Exclude Visa")
        self.btn_toggle_visa.setObjectName("btn_danger")
        self.btn_toggle_visa.setCheckable(True)
        self.btn_toggle_visa.clicked.connect(self._toggle_visa_section)
        
        v_top.addWidget(v_title)
        v_top.addStretch()
        v_top.addWidget(self.btn_toggle_visa)
        v_main_layout.addLayout(v_top)
        
        self.visa_content = QWidget()
        visa_layout = QFormLayout(self.visa_content)
        v_main_layout.addWidget(self.visa_content)
        self.v_type = QLineEdit("Umrah e-Visa")
        self.v_pax = QLineEdit("1")
        from PySide6.QtWidgets import QDoubleSpinBox
        self.v_purchase_price = QDoubleSpinBox()
        self.v_purchase_price.setMaximum(100000000)
        self.v_purchase_price.setPrefix("Cost: ")
        
        self.v_sales_price = QDoubleSpinBox()
        self.v_sales_price.setMaximum(100000000)
        self.v_sales_price.setPrefix("Sell: ")
        
        self.v_profit = QLineEdit("0")
        self.v_profit.setReadOnly(True)
        self.v_profit.setPlaceholderText("Profit")
        
        self.v_purchase_price.valueChanged.connect(self.calculate_visa_profit)
        self.v_sales_price.valueChanged.connect(self.calculate_visa_profit)
        
        visa_layout.addRow("Visa Type:", self.v_type)
        visa_layout.addRow("Passengers:", self.v_pax)
        visa_layout.addRow("Purchase Price:", self.v_purchase_price)
        visa_layout.addRow("Sales Price:", self.v_sales_price)
        visa_layout.addRow("Calculated Profit:", self.v_profit)
        self.modules_layout.addWidget(self.group_visa)
        
        # 3. Hotels Section
        self.hotels_wrapper = QWidget()
        self.hotels_container = QVBoxLayout(self.hotels_wrapper)
        self.hotels_container.setContentsMargins(0,0,0,0)
        btn_add_hotel = QPushButton("+ Add Hotel")
        btn_add_hotel.setObjectName("btn_secondary")
        btn_add_hotel.clicked.connect(self.add_hotel_widget)
        self.modules_layout.addWidget(QLabel("<b>Hotels</b>"))
        self.modules_layout.addWidget(self.hotels_wrapper)
        self.modules_layout.addWidget(btn_add_hotel)
        
        # 4. Transport Section
        self.trans_wrapper = QWidget()
        self.trans_container = QVBoxLayout(self.trans_wrapper)
        self.trans_container.setContentsMargins(0,0,0,0)
        btn_add_trans = QPushButton("+ Add Transport Leg")
        btn_add_trans.setObjectName("btn_secondary")
        btn_add_trans.clicked.connect(self.add_trans_widget)
        self.modules_layout.addWidget(QLabel("<b>Transport & Ziyarat</b>"))
        self.modules_layout.addWidget(self.trans_wrapper)
        self.modules_layout.addWidget(btn_add_trans)
        
        # Add initial dynamic widgets
        self.add_flight_widget()
        self.add_hotel_widget()
        self.add_trans_widget()
        
        self.modules_layout.addStretch()
        
        scroll.setWidget(modules_widget)
        builder_layout.addWidget(scroll)
        
        # Next Button
        btn_next = QPushButton("Proceed to Checkout ➔")
        btn_next.setObjectName("btn_primary")
        btn_next.setShortcut("Return")
        btn_next.setMinimumHeight(45)
        btn_next.clicked.connect(self.go_to_checkout)
        builder_layout.addWidget(btn_next)
        
        self.stacked_widget.addWidget(self.builder_widget)
        
        # --- SCREEN 2: CHECKOUT / INVOICE VIEW ---
        self.checkout_widget = QWidget()
        checkout_layout = QVBoxLayout(self.checkout_widget)
        
        btn_back = QPushButton("🡄 Back to Builder")
        btn_back.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        checkout_layout.addWidget(btn_back, alignment=Qt.AlignmentFlag.AlignLeft)
        
        self.lbl_checkout_title = QLabel("Checkout Summary")
        self.lbl_checkout_title.setObjectName("lbl_title")
        checkout_layout.addWidget(self.lbl_checkout_title)
        
        self.receipt_table = QTableWidget(0, 4)
        self.receipt_table.setHorizontalHeaderLabels(["Service Description", "Qty", "Unit Price", "Total"])
        self.receipt_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.receipt_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        checkout_layout.addWidget(self.receipt_table)
        
        self.lbl_grand_total = QLabel("Grand Total: PKR 0.00")
        self.lbl_grand_total.setStyleSheet("font-size: 18px; font-weight: bold; color: #48BB78;")
        checkout_layout.addWidget(self.lbl_grand_total, alignment=Qt.AlignmentFlag.AlignRight)
        

        # Action Buttons
        action_layout = QHBoxLayout()
        self.btn_confirm = QPushButton("✓ Confirm Booking")
        self.btn_confirm.setObjectName("btn_primary")
        self.btn_confirm.setShortcut("Return")
        self.btn_confirm.setMinimumHeight(45)
        self.btn_confirm.clicked.connect(self.save_booking)
        
        self.btn_save_edits = QPushButton("💾 Save Edits")
        self.btn_save_edits.setObjectName("btn_warning")
        self.btn_save_edits.setMinimumHeight(45)
        self.btn_save_edits.clicked.connect(self.save_booking)
        self.btn_save_edits.hide()
        
        self.btn_print = QPushButton("🖨 Print Invoice")
        self.btn_print.setMinimumHeight(45)
        self.btn_print.clicked.connect(self.print_invoice)
        self.btn_print.setEnabled(False)
        
        self.btn_print_voucher = QPushButton("🎟 Print Voucher")
        self.btn_print_voucher.setMinimumHeight(45)
        self.btn_print_voucher.clicked.connect(self.generate_voucher_pdf)
        self.btn_print_voucher.setEnabled(False)
        
        action_layout.addWidget(self.btn_confirm)
        action_layout.addWidget(self.btn_save_edits)
        action_layout.addWidget(self.btn_print)
        action_layout.addWidget(self.btn_print_voucher)
        checkout_layout.addLayout(action_layout)
        
        self.stacked_widget.addWidget(self.checkout_widget)
        main_layout.addWidget(self.stacked_widget)

    def calculate_base_profit(self):
        """
        Recalculate totals from the full pricing matrix in real time.

        Called whenever any QSpinBox (qty) or QLineEdit (price) in the
        Base Package group emits ``valueChanged`` / ``textChanged``.
        Updates the two live QLabel widgets inside the group box.
        """
        def _safe_float(text: str) -> float:
            try:
                return float(text.replace(",", "").strip() or 0)
            except ValueError:
                return 0.0

        a_qty  = self.spin_adult_qty.value()
        a_cost = _safe_float(self.t_adult_cost.text())
        a_sell = _safe_float(self.t_adult_sell.text())

        c_qty  = self.spin_child_qty.value()
        c_cost = _safe_float(self.t_child_cost.text())
        c_sell = _safe_float(self.t_child_sell.text())

        i_qty  = self.spin_infant_qty.value()
        i_cost = _safe_float(self.t_infant_cost.text())
        i_sell = _safe_float(self.t_infant_sell.text())

        total_cost    = (a_qty * a_cost) + (c_qty * c_cost) + (i_qty * i_cost)
        total_revenue = (a_qty * a_sell) + (c_qty * c_sell) + (i_qty * i_sell)
        net_profit    = total_revenue - total_cost

        profit_color = "#48BB78" if net_profit >= 0 else "#FC8181"  # green / red

        self.lbl_live_grand_total.setText(
            f"Grand Total:  PKR {total_revenue:,.2f}"
        )
        self.lbl_live_net_profit.setText(
            f"Net Profit:  PKR {net_profit:,.2f}"
        )
        self.lbl_live_net_profit.setStyleSheet(
            f"font-size: 13pt; font-weight: bold; color: {profit_color};"
        )


    def calculate_visa_profit(self):
        purchase = self.v_purchase_price.value()
        sales = self.v_sales_price.value()
        self.v_profit.setText(str(sales - purchase))
        
    def _toggle_visa_section(self):
        is_excluded = self.btn_toggle_visa.isChecked()
        self.visa_content.setVisible(not is_excluded)
        if is_excluded:
            self.btn_toggle_visa.setText("➕ Include Visa")
            self.btn_toggle_visa.setObjectName("btn_success")
        else:
            self.btn_toggle_visa.setText("✖ Exclude Visa")
            self.btn_toggle_visa.setObjectName("btn_danger")
        self.btn_toggle_visa.style().unpolish(self.btn_toggle_visa)
        self.btn_toggle_visa.style().polish(self.btn_toggle_visa)

    # ------------------------------------------------------------------ #
    # PAX ROSTER — Phase 3 auto-generator                                 #
    # ------------------------------------------------------------------ #

    _PAX_TYPE_COLORS = {
        "Adult":  "#60A5FA",   # blue
        "Child":  "#34D399",   # green
        "Infant": "#FBBF24",   # amber
    }

    def sync_pax_from_matrix(self):
        """
        Rebuild the PAX roster to exactly match the qty spinboxes.

        Algorithm
        ---------
        1. Read the three qty values from the pricing matrix.
        2. Build the *desired* ordered list of pax_types, e.g.
           [Adult×8, Child×1, Infant×1] → list of 10 type strings.
        3. Diff against the existing pax_widgets list:
           • Keep rows whose pax_type badge already matches the desired slot
             and preserve whatever the agent has already typed into them.
           • Append new blank rows for any extra slots.
           • Trim trailing rows that are no longer needed.

        This means the agent never loses data they have already entered —
        only the slot *count* changes.
        """
        a_qty = self.spin_adult_qty.value()
        c_qty = self.spin_child_qty.value()
        i_qty = self.spin_infant_qty.value()

        # Build target list in order: Adults first, then Children, Infants
        desired: list[str] = (
            ["Adult"]  * a_qty
            + ["Child"]  * c_qty
            + ["Infant"] * i_qty
        )
        current_len = len(self.pax_widgets)
        desired_len = len(desired)

        # --- Trim excess rows from the bottom -------------------------
        while len(self.pax_widgets) > desired_len:
            self.remove_pax_row(silent=True)

        # --- Update pax_type badge on existing rows -------------------
        for idx, pax_type in enumerate(desired[:current_len]):
            row_data = self.pax_widgets[idx]
            self._set_pax_type_badge(row_data["type_badge"], pax_type)
            row_data["pax_type"] = pax_type

        # --- Append new blank rows ------------------------------------
        for idx in range(current_len, desired_len):
            self.add_pax_row(pax_type=desired[idx])

        self._update_group_leader_dropdown()

    def add_pax_row(self, pax_type: str = "Adult"):
        """
        Append one typed passenger row to the scroll area.

        Parameters
        ----------
        pax_type : str
            One of ``"Adult"``, ``"Child"``, or ``"Infant"``.
            Drives the colour-coded lock badge shown on the left of each row.
        """
        pax_row_widget = QWidget()
        row_layout = QHBoxLayout(pax_row_widget)
        row_layout.setContentsMargins(0, 4, 0, 4)
        row_layout.setSpacing(6)

        # ── Pax-type badge (locked QComboBox) ─────────────────────────
        type_badge = QComboBox()
        type_badge.addItems(["Adult", "Child", "Infant"])
        type_badge.setFixedWidth(90)
        self._set_pax_type_badge(type_badge, pax_type)

        # ── Name field with autocomplete ──────────────────────────────
        name_edit = QLineEdit()
        name_edit.setPlaceholderText("Passenger Name")

        from PySide6.QtWidgets import QCompleter
        completer = QCompleter(self.pax_names_list, name_edit)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        _dropdown_style = """
            QAbstractItemView {
                background-color: #1E1E2E;
                color: #FFFFFF;
                selection-background-color: #FF512F;
                selection-color: #FFFFFF;
                border: 1px solid #333344;
                border-radius: 5px;
                outline: 0px;
                padding: 5px;
            }
            QAbstractItemView::item { padding: 8px; border-radius: 3px; }
            QAbstractItemView::item:hover { background-color: #2D2D44; }
        """
        popup = completer.popup()
        if popup:
            popup.setStyleSheet(_dropdown_style)
        name_edit.setCompleter(completer)

        # ── Passport field ────────────────────────────────────────────
        passport_edit = QLineEdit()
        passport_edit.setPlaceholderText("Passport No")

        # Auto-fill passport when a known name is chosen
        def on_name_changed(text):
            if text in self.pax_passport_map:
                passport_edit.setText(self.pax_passport_map[text])
            self._update_group_leader_dropdown()

        name_edit.textChanged.connect(on_name_changed)

        # ── Group no ──────────────────────────────────────────────────
        group_edit = QLineEdit()
        group_edit.setPlaceholderText("Group No")

        row_layout.addWidget(type_badge)
        row_layout.addWidget(name_edit, 3)
        row_layout.addWidget(passport_edit, 2)
        row_layout.addWidget(group_edit, 1)

        self.pax_container_layout.addWidget(pax_row_widget)
        self.pax_widgets.append({
            "widget":     pax_row_widget,
            "type_badge": type_badge,
            "pax_type":   pax_type,
            "name":       name_edit,
            "passport":   passport_edit,
            "group":      group_edit,
        })

    @staticmethod
    def _set_pax_type_badge(badge: QComboBox, pax_type: str) -> None:
        """
        Apply the correct colour and selection to a pax-type badge ComboBox.

        The ComboBox is set to the right item and styled with a matching
        background colour so Adult / Child / Infant rows are visually distinct
        at a glance.  The widget remains interactive so the agent can override
        the category if needed (e.g. infant travelling without a seat).
        """
        _colors = {
            "Adult":  ("#1E3A5F", "#60A5FA"),   # dark-bg, text
            "Child":  ("#14352B", "#34D399"),
            "Infant": ("#3B2A05", "#FBBF24"),
        }
        bg, fg = _colors.get(pax_type, ("#1E1E2E", "#FFFFFF"))
        badge.setCurrentText(pax_type)
        badge.setStyleSheet(
            f"QComboBox {{ background-color: {bg}; color: {fg};"
            f" font-weight: bold; border-radius: 4px; padding: 2px 4px; }}"
            f"QComboBox::drop-down {{ border: none; }}"
        )


        
    def _update_group_leader_dropdown(self):
        current = self.cb_group_leader.currentText()
        self.cb_group_leader.blockSignals(True)
        self.cb_group_leader.clear()
        self.cb_group_leader.addItem("Select Group Leader...")
        for pax in self.pax_widgets:
            name = pax["name"].text().strip()
            if name:
                self.cb_group_leader.addItem(name)
        if current and self.cb_group_leader.findText(current) >= 0:
            self.cb_group_leader.setCurrentText(current)
        self.cb_group_leader.blockSignals(False)

    def _on_group_leader_selected(self, leader_name):
        if leader_name and leader_name != "Select Group Leader...":
            for pax in self.pax_widgets:
                pax["group"].setText(leader_name)
            
    def remove_pax_row(self, silent: bool = False):
        """Remove the last PAX row from the roster.

        Parameters
        ----------
        silent : bool
            When True, skip the group-leader dropdown refresh.  Used by
            ``sync_pax_from_matrix`` to avoid repeated refreshes during a
            bulk trim.
        """
        if self.pax_widgets:
            pax_data = self.pax_widgets.pop()
            widget = pax_data["widget"]
            self.pax_container_layout.removeWidget(widget)
            widget.deleteLater()
            if not silent:
                self._update_group_leader_dropdown()


    def add_flight_widget(self):
        w = FlightLegWidget()
        self.flights_container.addWidget(w)
        return w
        
    def add_hotel_widget(self):
        w = HotelStayWidget()
        self.hotels_container.addWidget(w)
        return w
        
    def add_trans_widget(self):
        w = TransportWidget()
        self.trans_container.addWidget(w)
        return w
        
    def clear_dynamic_widgets(self):
        # Clear flights
        while self.flights_container.count():
            item = self.flights_container.takeAt(0)
            if item:
                widget = item.widget()
                if widget:
                    widget.deleteLater()
        # Clear hotels
        while self.hotels_container.count():
            item = self.hotels_container.takeAt(0)
            if item:
                widget = item.widget()
                if widget:
                    widget.deleteLater()

    def load_templates(self):
        try:
            with get_session() as session:
                from models.umrah import UmrahPackageTemplate
                templates = session.query(UmrahPackageTemplate).filter_by(is_deleted=False).all()
                for t in templates:
                    self.cb_template.addItem(t.name, t.id)
        except Exception as e:
            QMessageBox.critical(self, "Template Load Error", str(e))

    def _apply_template_data(self):
        template_id = self.cb_template.currentData()
        if not template_id:
            return
            
        try:
            with get_session() as session:
                from models.umrah import UmrahPackageTemplate
                from sqlalchemy.orm import joinedload
                template = session.query(UmrahPackageTemplate).options(joinedload(UmrahPackageTemplate.pricing)).filter_by(id=template_id).first()
                
                if not template:
                    return
                    
                # Auto-fill Hotels
                self.clear_dynamic_widgets()
                
                if template.makkah_hotel and template.makkah_nights:
                    w_mak = self.add_hotel_widget()
                    w_mak.h_city.setCurrentText("Makkah")
                    w_mak.h_name.search_input.setText(template.makkah_hotel)
                    w_mak.h_checkout.setDate(w_mak.h_checkin.date().addDays(template.makkah_nights))
                    
                if template.medinah_hotel and template.medinah_nights:
                    w_med = self.add_hotel_widget()
                    w_med.h_city.setCurrentText("Medinah")
                    w_med.h_name.search_input.setText(template.medinah_hotel)
                    w_med.h_checkout.setDate(w_med.h_checkin.date().addDays(template.medinah_nights))
                    
                # Base Price — populate Adult tier selling price from template
                base_price = 0
                if template.pricing:
                    base_price = template.pricing[0].price_per_person
                self.t_adult_sell.setText(str(base_price))
                
        except Exception as e:
            QMessageBox.critical(self, "Auto-fill Error", str(e))

    def load_customers(self):
        self.cb_customer.clear()
        try:
            with get_session() as session:
                from models.customer import Customer
                from sqlalchemy.orm import joinedload
                
                customers = session.query(Customer).options(joinedload(Customer.family_members)).all()
                customer_data = []
                for c in customers:
                    display_name = f"{c.full_name} ({c.phone_primary})"
                    customer_data.append((display_name, c.id))
                    
                    # Add main customer to pax autocomplete
                    self.pax_names_list.append(c.full_name)
                    if c.passport_number:
                        self.pax_passport_map[c.full_name] = c.passport_number
                        
                    # Add family members to pax autocomplete
                    for fam in c.family_members:
                        if fam.full_name not in self.pax_names_list:
                            self.pax_names_list.append(fam.full_name)
                        if fam.passport_number:
                            self.pax_passport_map[fam.full_name] = fam.passport_number
                self.cb_customer.set_data(customer_data)
                            
        except Exception as e:
            QMessageBox.critical(self, "Customer Load Error", str(e))

    def open_new_customer_form(self):
        from ui.pages.customers.customer_form import CustomerForm
        dialog = CustomerForm(parent=self)
        if dialog.exec():
            # Reload customers to pick up the new one
            self.load_customers()

    def collect_payload(self):
        # Build JSON Payload
        from typing import Any

        def _safe_float(text: str) -> float:
            try:
                return float(text.replace(",", "").strip() or 0)
            except ValueError:
                return 0.0

        payload: dict[str, Any] = {'flights': [], 'hotels': [], 'passengers': []}

        # ── Categorical pricing matrix ─────────────────────────────────
        payload['adult_count']         = self.spin_adult_qty.value()
        payload['adult_cost_price']    = _safe_float(self.t_adult_cost.text())
        payload['adult_selling_price'] = _safe_float(self.t_adult_sell.text())

        payload['child_count']         = self.spin_child_qty.value()
        payload['child_cost_price']    = _safe_float(self.t_child_cost.text())
        payload['child_selling_price'] = _safe_float(self.t_child_sell.text())

        payload['infant_count']        = self.spin_infant_qty.value()
        payload['infant_cost_price']   = _safe_float(self.t_infant_cost.text())
        payload['infant_selling_price']= _safe_float(self.t_infant_sell.text())

        # Derived convenience values (used by go_to_checkout receipt preview)
        a, c, i = payload['adult_count'], payload['child_count'], payload['infant_count']
        payload['total_pilgrims'] = a + c + i or 1

        payload['base_package_price'] = (
            (a * payload['adult_selling_price'])
            + (c * payload['child_selling_price'])
            + (i * payload['infant_selling_price'])
        )
        payload['base_purchase_cost'] = (
            (a * payload['adult_cost_price'])
            + (c * payload['child_cost_price'])
            + (i * payload['infant_cost_price'])
        )
        payload['base_profit'] = payload['base_package_price'] - payload['base_purchase_cost']

        payload['template_id'] = self.cb_template.currentData()
        if hasattr(self, 'cb_payment_method'):
            payload['payment_method'] = self.cb_payment_method.currentText()

        for pax in self.pax_widgets:
            name     = pax["name"].text().strip()
            passport = pax["passport"].text().strip()
            group    = pax["group"].text().strip()
            # Read live badge value — respects manual overrides by the agent
            pax_type = pax["type_badge"].currentText() if "type_badge" in pax else pax.get("pax_type", "Adult")

            if name:
                payload['passengers'].append({
                    'full_name':       name,
                    'passport_number': passport,
                    'group_no':        group,
                    'pax_type':        pax_type,   # Phase 3 — saved to UmrahPilgrim.pax_type
                })

        # Collect Flights
        for i in range(self.flights_container.count()):
            w = None
            item = self.flights_container.itemAt(i)
            if item and item.widget():
                w = item.widget()
            if isinstance(w, FlightLegWidget):
                data = w.get_data()
                if data['airline'].strip() or data['sales_price'] > 0:
                    payload['flights'].append(data)

        # Collect Visa
        if not self.btn_toggle_visa.isChecked() and (
            self.v_type.text().strip()
            or float(self.v_sales_price.value() or 0) > 0
        ):
            payload['visa'] = {
                'type':           self.v_type.text(),
                'pax':            int(self.v_pax.text() or 1),
                'purchase_price': self.v_purchase_price.value(),
                'sales_price':    self.v_sales_price.value(),
                'profit':         float(self.v_profit.text() or 0),
            }

        # Collect Hotels
        for i in range(self.hotels_container.count()):
            w = None
            item = self.hotels_container.itemAt(i)
            if item and item.widget():
                w = item.widget()
            if isinstance(w, HotelStayWidget):
                data = w.get_data()
                if data['hotel_name'].strip() or data['sales_price'] > 0:
                    payload['hotels'].append(data)

        # Collect Transport
        payload['transport'] = []
        for i in range(self.trans_container.count()):
            w = None
            item = self.trans_container.itemAt(i)
            if item and item.widget():
                w = item.widget()
            if isinstance(w, TransportWidget):
                data = w.get_data()
                if data:
                    payload['transport'].append(data)

        return payload

    def go_to_checkout(self):
        if not self.cb_customer.currentData():
            QMessageBox.warning(self, "Validation", "Please select a Customer first.")
            return

        payload = self.collect_payload()
        if (
            not payload['flights']
            and not payload.get('visa')
            and not payload['hotels']
            and not payload.get('transport')
            and payload.get('base_package_price', 0) == 0
        ):
            QMessageBox.warning(
                self, "Validation",
                "Please configure at least one service or base package price."
            )
            return

        self.receipt_table.setRowCount(0)
        grand_total = 0.0
        row = 0

        # ── Categorical base package rows (Adult / Child / Infant) ──────
        _tier_cfg = [
            ("🧑 Umrah Package — Adult",  "adult"),
            ("👦 Umrah Package — Child",  "child"),
            ("👶 Umrah Package — Infant", "infant"),
        ]
        for label, key in _tier_cfg:
            qty  = payload.get(f"{key}_count", 0)
            sell = payload.get(f"{key}_selling_price", 0.0)
            if qty > 0 and sell > 0:
                subtotal = qty * sell
                grand_total += subtotal
                self.add_receipt_row(row, label, qty, sell, subtotal)
                row += 1

        # ── Flights ─────────────────────────────────────────────────────
        for f in payload['flights']:
            total = f['sales_price'] * f['pax']
            grand_total += total
            self.add_receipt_row(
                row,
                f"Flight [{f['leg_type']}] ({f['airline']})",
                f['pax'], f['sales_price'], total,
            )
            row += 1

        # ── Visa ────────────────────────────────────────────────────────
        if 'visa' in payload:
            v = payload['visa']
            total = v['sales_price'] * v['pax']
            grand_total += total
            self.add_receipt_row(row, f"Visa ({v['type']})", v['pax'], v['sales_price'], total)
            row += 1

        # ── Hotels ──────────────────────────────────────────────────────
        for h in payload['hotels']:
            grand_total += h['sales_price']
            self.add_receipt_row(
                row,
                f"Hotel [{h['city']}] ({h['hotel_name']})",
                1, h['sales_price'], h['sales_price'],
            )
            row += 1

        # ── Transport ───────────────────────────────────────────────────
        for t in payload.get('transport', []):
            grand_total += t['sales_price']
            self.add_receipt_row(
                row,
                f"Transport ({t['type']})",
                1, t['sales_price'], t['sales_price'],
            )
            row += 1

        self.lbl_grand_total.setText(f"Grand Total: PKR {grand_total:,.2f}")

        if self.is_edit_mode:
            self.btn_confirm.hide()
            self.btn_save_edits.show()
            self.btn_print.setEnabled(True)
            self.btn_print_voucher.setEnabled(True)
        else:
            self.btn_confirm.show()
            self.btn_save_edits.hide()
            self.btn_print.setEnabled(False)
            self.btn_print_voucher.setEnabled(False)

        self.stacked_widget.setCurrentIndex(1)
        
    def add_receipt_row(self, row, desc, qty, unit, total):
        self.receipt_table.insertRow(row)
        self.receipt_table.setItem(row, 0, QTableWidgetItem(desc))
        self.receipt_table.setItem(row, 1, QTableWidgetItem(str(qty)))
        self.receipt_table.setItem(row, 2, QTableWidgetItem(f"{unit:,.2f}"))
        self.receipt_table.setItem(row, 3, QTableWidgetItem(f"{total:,.2f}"))

    def save_booking(self):

        customer_id = self.cb_customer.currentData()
        payload = self.collect_payload()
        
        try:
            with get_session() as session:
                if self.is_edit_mode and self.current_booking_id:
                    umrah = self.checkout_service.update_unified_booking(session, self.current_booking_id, payload, "USER")
                    msg = "Booking updated successfully!"
                else:
                    umrah = self.checkout_service.create_unified_booking(session, customer_id, payload, "USER")
                    self.current_booking_id = umrah.id
                    self.is_edit_mode = True
                    msg = "Booking confirmed and Invoice generated!"
                    
                session.commit()
                
                # Broadcast the event so all background tabs auto-refresh
                from core.signals import app_signals
                app_signals.umrah_checkout_completed.emit()
                
                QMessageBox.information(self, "Success", msg)
                self.btn_confirm.hide()
                self.btn_save_edits.show()
                self.btn_print.setEnabled(True)
                self.btn_print_voucher.setEnabled(True)
                
        except Exception as e:
            QMessageBox.critical(self, "Database Error", str(e))

    def load_booking(self, booking_id: str):
        try:
            with get_session() as session:
                umrah = session.get(CustomUmrahBooking, booking_id)
                if not umrah:
                    QMessageBox.critical(self, "Error", "Booking not found.")
                    return
                    
                self.current_booking_id = booking_id
                self.is_edit_mode = True
                
                # Set Customer
                self.cb_customer.set_by_id(umrah.customer_id)
                    
                self.clear_dynamic_widgets()

                # ── Populate categorical pricing matrix ────────────────
                # Prefer values from the master Booking record (Phase 1
                # categorical columns).  Fall back to 0 for older records.
                master_booking = getattr(umrah, 'master_booking', None)
                if master_booking is None:
                    # Try to locate the Booking record linked to this Umrah booking
                    from models.booking import Booking as MasterBooking
                    master_booking = (
                        session.query(MasterBooking)
                        .filter_by(package_id=umrah.id, is_deleted=False)
                        .first()
                    )

                def _fmt(val) -> str:
                    try:
                        return f"{float(val or 0):.2f}"
                    except (TypeError, ValueError):
                        return "0.00"

                if master_booking:
                    self.spin_adult_qty.setValue(int(master_booking.adult_count or 0))
                    self.t_adult_cost.setText(_fmt(master_booking.adult_cost_price))
                    self.t_adult_sell.setText(_fmt(master_booking.adult_selling_price))

                    self.spin_child_qty.setValue(int(master_booking.child_count or 0))
                    self.t_child_cost.setText(_fmt(master_booking.child_cost_price))
                    self.t_child_sell.setText(_fmt(master_booking.child_selling_price))

                    self.spin_infant_qty.setValue(int(master_booking.infant_count or 0))
                    self.t_infant_cost.setText(_fmt(master_booking.infant_cost_price))
                    self.t_infant_sell.setText(_fmt(master_booking.infant_selling_price))
                else:
                    # Legacy fallback — spread the total across Adults only
                    total_pax = int(getattr(umrah, 'total_pilgrims', 1) or 1)
                    self.spin_adult_qty.setValue(total_pax)
                    self.t_adult_cost.setText(_fmt(getattr(umrah, 'base_purchase_cost', 0.0)))
                    self.t_adult_sell.setText(_fmt(getattr(umrah, 'base_package_price', 0.0)))

                # Voucher Metadata
                self.v_voucher_no.setText(f"HV-{umrah.booking_number}")

                if umrah.template:
                    self.v_pkg_category.setCurrentText(umrah.template.name)
                else:
                    self.v_pkg_category.setCurrentText("CUSTOM UMRAH")
                self.v_issue_date.setDate(QDate.currentDate())
                
                # Parse Invoice for PAX heuristics
                invoice = session.query(Invoice).filter_by(reference_id=umrah.id).first()
                
                # Clear pax widgets
                while self.pax_widgets:
                    self.remove_pax_row()

                if umrah.pilgrims:
                    for p in umrah.pilgrims:
                        # pax_type stored by Phase 1 — fallback to 'Adult' for legacy rows
                        saved_type = getattr(p, 'pax_type', None) or "Adult"
                        # Normalise in case legacy DB stored lowercase/enum value
                        saved_type = str(saved_type).capitalize() if saved_type else "Adult"
                        if saved_type not in ("Adult", "Child", "Infant"):
                            saved_type = "Adult"

                        self.add_pax_row(pax_type=saved_type)
                        last_pax = self.pax_widgets[-1]
                        last_pax["name"].setText(p.full_name or "")
                        last_pax["passport"].setText(p.passport_number or "")
                        last_pax["group"].setText(p.group_no or "")

                # Fill Flights
                if not umrah.flights:
                    self.add_flight_widget()
                else:
                    for f in umrah.flights:
                        w = self.add_flight_widget()
                        w.f_leg_type.setCurrentText(f.leg_type)
                        w.f_airline.setText(f.airline)
                        w.f_flight_number.setText(f.flight_number or "")
                        w.f_origin.setText(f.origin)
                        w.f_dest.setText(f.destination)
                        if f.departure_time:
                            w.f_dep_time.setTime(QTime.fromString(f.departure_time, "HH:mm"))
                        if f.arrival_time:
                            w.f_arr_time.setTime(QTime.fromString(f.arrival_time, "HH:mm"))
                        w.f_pnr.setText(f.pnr or "")
                        w.f_sales_price.setValue(float(f.selling_price or 0.0))
                        w.f_purchase_price.setValue(float(f.purchase_price or 0.0))
                        # Estimate pax
                        pax = 1
                        if invoice:
                            for item in invoice.items:
                                if "Flight" in item.description and f.airline in item.description:
                                    pax = item.quantity
                        w.f_pax.setText(str(pax))
                        
                # Fill Visa
                self.v_type.setText("")
                self.v_sales_price.setValue(0)
                if umrah.visas:
                    v = umrah.visas[0]
                    self.v_type.setText(v.visa_type)
                    pax = 1
                    if invoice:
                        for item in invoice.items:
                            if "Visa" in item.description:
                                pax = item.quantity
                    self.v_pax.setText(str(pax))
                    self.v_sales_price.setValue(v.total_cost)
                    
                # Fill Hotels
                if not umrah.hotels:
                    self.add_hotel_widget()
                else:
                    for h in umrah.hotels:
                        w = self.add_hotel_widget()
                        w.h_city.setCurrentText(h.city)
                        w.h_name.search_input.setText(h.hotel_name_override or h.notes or "")
                        w.h_hn_number.setText(h.hn_number or "")
                        w.h_reservation_name.setText(h.reservation_name or "")
                        w.h_room_type.setCurrentText(h.room_type or "DOUBLE")
                        w.h_rooms_count.setText(str(h.num_rooms or 1))
                        w.h_checkin.setDate(QDate(h.check_in_date.year, h.check_in_date.month, h.check_in_date.day))
                        w.h_checkout.setDate(QDate(h.check_out_date.year, h.check_out_date.month, h.check_out_date.day))
                        w.h_sales_price.setValue(float(h.total_selling or 0.0))
                        w.h_purchase_price.setValue(float(h.purchase_price or 0.0))
                        
                # Find Transport
                # Clear existing transports
                while self.trans_container.count():
                    child = self.trans_container.takeAt(0)
                    if child:
                        widget = child.widget()
                        if widget:
                            widget.deleteLater()
                        
                if umrah.transport_details:
                    tds = umrah.transport_details
                    if isinstance(tds, dict):
                        tds = [tds]
                    for td in tds:
                        w = self.add_trans_widget()
                        w.load_data(td)
                elif invoice:
                    for item in invoice.items:
                        if "Transport" in item.description:
                            w = self.add_trans_widget()
                            w.t_type.setCurrentText(item.description.replace("Transport - ", ""))
                            w.t_sales_price.setValue(item.unit_price)
                            
        except Exception as e:
            QMessageBox.critical(self, "Load Error", str(e))

    def print_invoice(self):
        if not self.current_booking_id:
            return
            
        try:
            with get_session() as session:
                from sqlalchemy.orm import joinedload
                from sqlalchemy import select
                stmt = select(Invoice).options(
                    joinedload(Invoice.customer),
                    joinedload(Invoice.items),
                    joinedload(Invoice.payment_transactions)
                ).where(Invoice.reference_id == self.current_booking_id)
                invoice = session.scalars(stmt).first()
                
                if not invoice:
                    QMessageBox.warning(self, "Error", "Invoice not found for this booking.")
                    return
                
                umrah_booking = session.get(CustomUmrahBooking, self.current_booking_id)

                os.makedirs("reports/output", exist_ok=True)
                pdf_path = os.path.abspath(f"reports/output/{invoice.invoice_number}.pdf")
                InvoiceGenerator.generate_umrah_group_invoice_pdf(invoice, pdf_path, umrah_booking=umrah_booking)
                
                os.startfile(pdf_path)
                
        except Exception as e:
            QMessageBox.critical(self, "Print Error", str(e))

    def generate_voucher_pdf(self):
        if not self.current_booking_id:
            return
            
        try:
            with get_session() as session:
                umrah = session.get(CustomUmrahBooking, self.current_booking_id)
                if not umrah:
                    QMessageBox.warning(self, "Error", "Booking not found.")
                    return
                
                customer = umrah.customer
                
                import datetime
                import sys
                from utils.pdf_generator import VoucherBuilder
                
                payload = self.collect_payload()
                
                issue_date_str = self.v_issue_date.date().toString("dd/MM/yyyy")
                pkg_cat = self.v_pkg_category.currentText()
                v_no = self.v_voucher_no.text().strip() or f"HV-{umrah.booking_number}"
                
                data = {
                    'voucher_no': v_no,
                    'issue_date': issue_date_str,
                    'pkg_category': pkg_cat,
                    'print_dt': datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                    'branch_office': "HAMZA NAWABSHAH - UMRAH",
                    'passengers': [],
                    'accommodation': [],
                    'transport': [],
                    'flights': []
                }
                
                # Passengers
                if umrah.pilgrims:
                    for p in umrah.pilgrims:
                        data['passengers'].append({
                            'name': p.full_name,
                            'passport': p.passport_number,
                            'group': p.group_no or (customer.full_name if customer else 'N/A')
                        })
                else:
                    data['passengers'].append({
                        'name': customer.full_name,
                        'passport': 'N/A',
                        'group': customer.full_name
                    })
                    
                # Accommodation
                for h in payload.get('hotels', []):
                    if h.get('hotel_name', '').strip():
                        nights = (h['check_out_date'] - h['check_in_date']).days
                        data['accommodation'].append({
                            'city': h['city'],
                            'hn': h.get('hn_number') or str(len(data['accommodation'])+1),
                            'hotel_name': h['hotel_name'],
                            'room': h.get('rooms_count', 1),
                            'room_type': h.get('room_type', 'DOUBLE'),
                            'check_in': h['check_in_date'].strftime("%d/%m/%Y"),
                            'check_out': h['check_out_date'].strftime("%d/%m/%Y"),
                            'nights': nights,
                            'reservation_name': h.get('reservation_name', '')
                        })
                            
                # Transport
                for t in payload.get('transport', []):
                    pickup = t.get('pickup_date')
                    if hasattr(pickup, 'strftime'):
                        pickup_str = pickup.strftime("%d/%m/%Y")
                    else:
                        pickup_str = str(pickup) if pickup else datetime.date.today().strftime("%d/%m/%Y")
                        
                    data['transport'].append({
                        'tn': t.get('tn_number') or '1',
                        'service': t.get('service_route') or 'UMRAH ROUTE',
                        'vehicle': t.get('type'),
                        'pickup_date': pickup_str,
                        'contact': t.get('contact_person') or 'N/A',
                        'ref_no': t.get('booking_ref') or f"TR-{umrah.booking_number}"
                    })
                    
                # Flights
                for f in payload.get('flights', []):
                    if f.get('airline', '').strip():
                        dep_date = f.get('departure_date')
                        if hasattr(dep_date, 'strftime'):
                            date_str = dep_date.strftime("%d/%m/%Y")
                        else:
                            date_str = str(dep_date) if dep_date else datetime.date.today().strftime("%d/%m/%Y")
                            
                        data['flights'].append({
                            'pnr': f.get('pnr') or 'TBA',
                            'date': date_str,
                            'flight': f.get('flight_number') or f.get('airline'),
                            'from': f.get('origin'),
                            'to': f.get('destination'),
                            'dep': f.get('departure_time') or 'TBA',
                            'arr': f.get('arrival_time') or 'TBA'
                        })
                            
                builder = VoucherBuilder(data, filename=f"Voucher_{umrah.booking_number}.pdf")
                pdf_path = builder.generate()
                
                if os.name == 'nt':
                    os.startfile(pdf_path)
                elif sys.platform == 'darwin':
                    import subprocess
                    subprocess.call(('open', pdf_path))
                else:
                    import subprocess
                    subprocess.call(('xdg-open', pdf_path))
                    
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Print Error", str(e))
