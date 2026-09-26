from typing import Dict, Any, List
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QLineEdit, QFormLayout, QComboBox, QDateEdit, QTimeEdit,
    QMessageBox, QGroupBox, QWidget, QSpinBox, QScrollArea, QFrame, QDoubleSpinBox
)
from PySide6.QtCore import Qt, QDate, QTime
from viewmodels.flight_viewmodel import FlightViewModel
from services.customer_service import CustomerService
from ui.components.searchable_combo_box import SearchableComboBox

class FlightFormDialog(QDialog):
    def __init__(self, current_user_id, flight=None, parent=None):
        super().__init__(parent)
        self.current_user_id = current_user_id
        self.flight = flight
        self.setWindowTitle("Flight Booking Form")
        self.setMinimumSize(900, 700)
        
        self.viewmodel = FlightViewModel()
        self.viewmodel.flight_saved.connect(self._on_saved)
        self.viewmodel.error_occurred.connect(self._on_error)
        
        self.pax_widgets = []
        self._setup_ui()
        
        if self.flight:
            self._populate_fields()
            
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(15)
        
        # 1. Basic Info
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)
        
        self.customer_cb = SearchableComboBox()
        self.customer_cb.search_input.setPlaceholderText("Search Customer...")
        basic_layout.addRow("Customer *:", self.customer_cb)
        
        self.trip_type_cb = QComboBox()
        self.trip_type_cb.addItems(["One Way", "Round Trip", "Multi City"])
        basic_layout.addRow("Trip Type *:", self.trip_type_cb)
        
        self.flight_type_cb = QComboBox()
        self.flight_type_cb.addItems(["Domestic", "International"])
        basic_layout.addRow("Flight Type *:", self.flight_type_cb)
        layout.addWidget(basic_group)
        
        # 2. Flight Details (Flat Info UI)
        flight_group = QGroupBox("Flight Details")
        flight_layout = QFormLayout(flight_group)
        
        self.leg_type = QComboBox()
        self.leg_type.addItems(["Outbound", "Return", "Transit", "Multi-City"])
        
        self.airline = QLineEdit()
        self.airline.setPlaceholderText("e.g. Saudi Airlines")
        self.flight_number = QLineEdit()
        self.flight_number.setPlaceholderText("Flight No (e.g. PK-831)")
        self.origin = QLineEdit()
        self.origin.setPlaceholderText("Origin (e.g. KHI)")
        self.destination = QLineEdit()
        self.destination.setPlaceholderText("Destination (e.g. JED)")
        
        self.flight_date = QDateEdit(QDate.currentDate())
        self.flight_date.setCalendarPopup(True)
        
        self.dep_time = QTimeEdit(QTime.currentTime())
        self.arr_time = QTimeEdit(QTime.currentTime().addSecs(3600 * 2))
        
        self.pnr_input = QLineEdit()
        self.pnr_input.setPlaceholderText("PNR (Optional)")
        
        flight_layout.addRow("Leg Type:", self.leg_type)
        flight_layout.addRow("Airline *:", self.airline)
        flight_layout.addRow("Flight No:", self.flight_number)
        flight_layout.addRow("Origin *:", self.origin)
        flight_layout.addRow("Destination *:", self.destination)
        flight_layout.addRow("Flight Date:", self.flight_date)
        flight_layout.addRow("Dep Time:", self.dep_time)
        flight_layout.addRow("Arr Time:", self.arr_time)
        flight_layout.addRow("PNR:", self.pnr_input)
        
        layout.addWidget(flight_group)
        
        # 3. Passengers Details
        pax_group = QGroupBox("Passengers")
        pax_layout = QVBoxLayout(pax_group)
        
        ctrl_layout = QHBoxLayout()
        ctrl_layout.addWidget(QLabel("Number of Passengers:"))
        self.pax_spin = QSpinBox()
        self.pax_spin.setRange(1, 40)
        self.pax_spin.setValue(1)
        self.pax_spin.valueChanged.connect(self._update_pax_forms)
        ctrl_layout.addWidget(self.pax_spin)
        ctrl_layout.addStretch()
        pax_layout.addLayout(ctrl_layout)
        
        self.pax_container = QWidget()
        self.pax_container_layout = QVBoxLayout(self.pax_container)
        self.pax_container_layout.setContentsMargins(0,0,0,0)
        pax_layout.addWidget(self.pax_container)
        layout.addWidget(pax_group)
        
        # 4. Financials
        fin_group = QGroupBox("Financials")
        fin_layout = QFormLayout(fin_group)
        
        self.purchase_price = QDoubleSpinBox()
        self.purchase_price.setMaximum(100000000)
        self.purchase_price.setPrefix("PKR ")
        
        self.sales_price = QDoubleSpinBox()
        self.sales_price.setMaximum(100000000)
        self.sales_price.setPrefix("PKR ")
        
        self.profit = QLineEdit("0.0")
        self.profit.setReadOnly(True)
        self.profit.setPlaceholderText("Profit")
        
        self.purchase_price.valueChanged.connect(self.calculate_profit)
        self.sales_price.valueChanged.connect(self.calculate_profit)
        
        self.notes = QLineEdit()
        self.notes.setPlaceholderText("Internal Notes")
        
        fin_layout.addRow("Purchase Price:", self.purchase_price)
        fin_layout.addRow("Sales Price *:", self.sales_price)
        fin_layout.addRow("Calculated Profit:", self.profit)
        fin_layout.addRow("Internal Notes:", self.notes)
        layout.addWidget(fin_group)
        
        layout.addStretch()
        scroll.setWidget(container)
        main_layout.addWidget(scroll)
        
        # 5. Buttons
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Save Booking")
        btn_save.setObjectName("btn_primary")
        btn_save.setMinimumHeight(40)
        btn_save.setDefault(True)
        btn_save.clicked.connect(self._build_and_save)
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setMinimumHeight(40)
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        main_layout.addLayout(btn_layout)
        
        # Initialize
        self._populate_customers()
        self._update_pax_forms(1)

    def calculate_profit(self):
        purchase = self.purchase_price.value()
        sales = self.sales_price.value()
        self.profit.setText(str(sales - purchase))
            
    def _populate_customers(self):
        from core.base_viewmodel import WorkerThread
        self.worker = WorkerThread(lambda: CustomerService().search_customers(limit=1000))
        self.worker.finished_signal.connect(self._on_customers_loaded)
        self.worker.error_signal.connect(lambda e: setattr(self, "customer_map", {}))
        self.worker.start()
        
    def _on_customers_loaded(self, customers):
        current_text = self.customer_cb.search_input.text()
        self.customer_cb.search_input.clear()
        if isinstance(customers, dict):
            customers = customers.get("items", [])
        self.customer_map = {c.full_name: c.id for c in customers}
        if self.customer_map:
            self.customer_cb.set_data([(c.full_name, c.id) for c in customers])
            if current_text:
                self.customer_cb.search_input.setText(current_text)
        else:
            if not current_text:
                self.customer_cb.search_input.setText("No customers found")
                
    def _update_pax_forms(self, count):
        while self.pax_container_layout.count():
            item = self.pax_container_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        self.pax_widgets.clear()
        
        for i in range(count):
            gb = QFrame()
            gb.setFrameShape(QFrame.Shape.StyledPanel)
            gb.setStyleSheet("QFrame { background-color: #2D3748; border-radius: 5px; margin-bottom: 5px; }")
            
            fl = QFormLayout(gb)
            
            lbl_title = QLabel(f"<b>Passenger {i+1}</b>")
            fl.addRow(lbl_title)
            
            title = QComboBox()
            title.addItems(["Mr", "Mrs", "Ms", "Mstr", "Miss"])
            fn = QLineEdit()
            ln = QLineEdit()
            pass_num = QLineEdit()
            ticket_num = QLineEdit()
            
            fl.addRow("Title:", title)
            fl.addRow("First Name *:", fn)
            fl.addRow("Last Name *:", ln)
            fl.addRow("Passport #:", pass_num)
            fl.addRow("Ticket #:", ticket_num)
            
            self.pax_container_layout.addWidget(gb)
            self.pax_widgets.append({
                "title": title, "first_name": fn, "last_name": ln,
                "passport": pass_num, "ticket": ticket_num
            })

    def _populate_fields(self):
        f = self.flight
        if getattr(f, "customer", None):
            self.customer_cb.search_input.setText(f.customer.full_name)
            
        self.trip_type_cb.setCurrentText(getattr(f, "trip_type", "One Way"))
        self.flight_type_cb.setCurrentText(getattr(f, "flight_type", "Domestic"))
        
        # Flight Details
        self.leg_type.setCurrentText(getattr(f, "leg_type", "Outbound"))
        self.airline.setText(getattr(f, "airline", "") or "")
        self.flight_number.setText(getattr(f, "flight_number", "") or "")
        self.origin.setText(getattr(f, "origin", "") or "")
        self.destination.setText(getattr(f, "destination", "") or "")
        
        if getattr(f, "departure_date", None):
            val = f.departure_date
            if isinstance(val, str):
                self.flight_date.setDate(QDate.fromString(val, Qt.DateFormat.ISODate))
            else:
                self.flight_date.setDate(val)
                
        if getattr(f, "departure_time", None):
            t = QTime.fromString(f.departure_time, "HH:mm")
            if t.isValid(): self.dep_time.setTime(t)
            
        if getattr(f, "arrival_time", None):
            t = QTime.fromString(f.arrival_time, "HH:mm")
            if t.isValid(): self.arr_time.setTime(t)
            
        self.pnr_input.setText(getattr(f, "pnr", "") or "")
        
        # Financials
        self.purchase_price.setValue(float(getattr(f, "purchase_price", 0) or 0))
        self.sales_price.setValue(float(getattr(f, "sales_price", 0) or getattr(f, "selling_price", 0) or 0))
        self.calculate_profit()
        self.notes.setText(getattr(f, "notes", "") or "")
        
        # Passengers
        passengers = getattr(f, "passengers", [])
        if passengers:
            self.pax_spin.setValue(len(passengers))
            for i, pax in enumerate(passengers):
                w = self.pax_widgets[i]
                w["title"].setCurrentText(getattr(pax, "title", "") or "Mr")
                w["first_name"].setText(getattr(pax, "first_name", "") or "")
                w["last_name"].setText(getattr(pax, "last_name", "") or "")
                w["passport"].setText(getattr(pax, "passport_number", "") or "")
                w["ticket"].setText(getattr(pax, "ticket_number", "") or "")

    def _build_and_save(self):
        # Validate
        if not self.customer_cb.search_input.text():
            QMessageBox.warning(self, "Error", "Please select a customer.")
            return
            
        if not self.airline.text().strip() or not self.origin.text().strip() or not self.destination.text().strip():
            QMessageBox.warning(self, "Error", "Airline, Origin, and Destination are required.")
            return
            
        for idx, w in enumerate(self.pax_widgets):
            if not w["first_name"].text().strip() or not w["last_name"].text().strip():
                QMessageBox.warning(self, "Error", f"First Name and Last Name are required for Passenger {idx+1}.")
                return
                
        if self.sales_price.value() <= 0:
            QMessageBox.warning(self, "Error", "Selling price must be greater than 0.")
            return
            
        self.setEnabled(False)
        
        customer_name = self.customer_cb.search_input.text()
        customer_id = self.customer_map.get(customer_name, None)
        
        booking_data = {
            "id": self.flight.id if self.flight else None,
            "customer_id": customer_id,
            "flight_type": self.flight_type_cb.currentText(),
            "trip_type": self.trip_type_cb.currentText(),
            
            "leg_type": self.leg_type.currentText(),
            "airline": self.airline.text().strip(),
            "flight_number": self.flight_number.text().strip(),
            "origin": self.origin.text().strip(),
            "destination": self.destination.text().strip(),
            "departure_date": self.flight_date.date().toPython(),
            "departure_time": self.dep_time.time().toString("HH:mm"),
            "arrival_time": self.arr_time.time().toString("HH:mm"),
            
            "pnr": self.pnr_input.text().strip(),
            
            "purchase_price": self.purchase_price.value(),
            "sales_price": self.sales_price.value(),
            "selling_price": self.sales_price.value(),
            "profit": float(self.profit.text() or 0),
            "notes": self.notes.text().strip()
        }
                
        passengers_data = []
        for i, w in enumerate(self.pax_widgets):
            passengers_data.append({
                "title": w["title"].currentText(),
                "first_name": w["first_name"].text().strip(),
                "last_name": w["last_name"].text().strip(),
                "passport_number": w["passport"].text().strip(),
                "ticket_number": w["ticket"].text().strip(),
                "is_primary": (i == 0)
            })
            
        self.viewmodel.save_flight(booking_data, passengers_data=passengers_data, current_user_id=self.current_user_id)

    def _on_saved(self, result):
        try:
            from services.accounting_service import AccountingService
            from config.database import get_session
            from models.flight import FlightBooking
            from models.booking import Booking
            import os
            import datetime
            from services.invoice_generator import InvoiceGenerator
            from utils.pdf_generator import VoucherBuilder
            
            with get_session() as session:
                flight = session.query(FlightBooking).get(result.id)
                if flight:
                    central = Booking(
                        booking_type="Flight_Only",
                        customer_id=flight.customer_id,
                        cost_price=flight.purchase_price or 0,
                        selling_price=flight.sales_price or 0,
                        details=f"Flight PNR: {flight.pnr}"
                    )
                    session.add(central)
                    session.commit()
                    
                    if flight.selling_price > 0:
                        invoice = AccountingService().post_standalone_booking(
                            customer_id=flight.customer_id,
                            total_amount=flight.selling_price,
                            item_description=f"Flight Booking - PNR: {flight.pnr}",
                            created_by=self.current_user_id
                        )
                        # Generate Invoice PDF
                        os.makedirs("invoices", exist_ok=True)
                        inv_path = os.path.abspath(f"invoices/Invoice_{invoice.invoice_number}.pdf")
                        InvoiceGenerator.generate_invoice_pdf(invoice, inv_path)
                        if hasattr(os, 'startfile'):
                            os.startfile(inv_path)

                    # Generate Voucher PDF
                    v_data = {
                        'voucher_no': f"FV-{flight.id[:6].upper()}",
                        'issue_date': datetime.datetime.now().strftime("%d/%m/%Y"),
                        'pkg_category': 'FLIGHT ONLY',
                        'print_dt': datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                        'branch_office': 'MAIN OFFICE',
                        'passengers': [
                            {'name': f"{p.first_name} {p.last_name}", 'passport': p.passport_number or "", 'group': ''}
                            for p in flight.passengers
                        ],
                        'accommodation': [],
                        'transport': [],
                        'flights': [
                            {
                                'pnr': flight.pnr or '',
                                'date': flight.departure_date.strftime("%d/%m/%Y") if hasattr(flight.departure_date, 'strftime') else str(flight.departure_date),
                                'flight': flight.flight_number or '',
                                'from': flight.origin or '',
                                'to': flight.destination or '',
                                'dep': flight.departure_time or '',
                                'arr': flight.arrival_time or ''
                            }
                        ]
                    }
                    filename = f"Flight_Voucher_{flight.pnr or flight.id[:8]}.pdf"
                    voucher_path = VoucherBuilder(v_data, filename=filename).generate()
                    if hasattr(os, 'startfile'):
                        os.startfile(voucher_path)

                    from core.signals import app_signals
                    app_signals.flight_added.emit()
                    
        except Exception as e:
            QMessageBox.warning(self, "Accounting Error", f"Flight saved but failed to generate invoice/booking: {str(e)}")
            
        self.accept()

    def _on_error(self, message):
        self.setEnabled(True)
        QMessageBox.critical(self, "Error", message)
