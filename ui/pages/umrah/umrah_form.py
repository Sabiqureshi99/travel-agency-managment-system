import json
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QLineEdit, QFormLayout, QComboBox, 
                               QDateEdit, QMessageBox, QGroupBox, QGridLayout,
                               QTableWidget, QTableWidgetItem, QHeaderView, 
                               QSpinBox, QTextEdit)
from PySide6.QtCore import Qt, QDate
from viewmodels.umrah_viewmodel import UmrahViewModel

class CustomUmrahBookingWizard(QDialog):
    def __init__(self, current_user_id="system", parent=None):
        super().__init__(parent)
        self.current_user_id = current_user_id
        self.viewmodel = UmrahViewModel()
        
        # Connections
        self.viewmodel.booking_saved.connect(self._on_saved)
        self.viewmodel.pricing_loaded.connect(self._on_pricing_loaded)
        self.viewmodel.form_data_loaded.connect(self._on_form_data_loaded)
        self.viewmodel.error_occurred.connect(self._on_error)
        
        self.template_pricing_cache = []
        self.customer_map = {}
        self.template_map = {}
        self.template_nights = {} # Store total nights for dynamic calc
        
        self.init_ui()
        self.viewmodel.load_form_data()

    def init_ui(self):
        self.setWindowTitle("Custom Umrah Booking Wizard")
        self.setMinimumSize(900, 700)
        
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        
        # Step 1: Customer & Template Selection
        step1_group = QGroupBox("1. Customer & Template Selection")
        step1_group.setMaximumWidth(600)
        step1_layout = QGridLayout(step1_group)
        step1_layout.setSpacing(15)
        
        self.customer_cb = QComboBox()
        self.customer_cb.addItem("Loading...")
        
        self.template_cb = QComboBox()
        self.template_cb.addItem("Loading...")
        self.template_cb.currentIndexChanged.connect(self._on_template_selected)
        
        self.bkg_date = QDateEdit(QDate.currentDate())
        self.bkg_date.setCalendarPopup(True)
        
        step1_layout.addWidget(QLabel("Customer *:"), 0, 0)
        step1_layout.addWidget(self.customer_cb, 0, 1)
        step1_layout.addWidget(QLabel("Booking Date:"), 0, 2)
        step1_layout.addWidget(self.bkg_date, 0, 3)
        step1_layout.addWidget(QLabel("Master Template:"), 1, 0)
        step1_layout.addWidget(self.template_cb, 1, 1)
        
        main_layout.addWidget(step1_group)
        
        # Step 2: Customization (Pricing Matrix Selection)
        step2_group = QGroupBox("2. Package Configuration")
        step2_group.setMaximumWidth(600)
        step2_layout = QGridLayout(step2_group)
        step2_layout.setSpacing(15)
        
        self.pricing_opts_cb = QComboBox()
        self.pricing_opts_cb.currentIndexChanged.connect(self._recalc_total)
        
        self.dep_date = QDateEdit(QDate.currentDate().addDays(15))
        self.dep_date.setCalendarPopup(True)
        
        self.total_pilgrims = QSpinBox()
        self.total_pilgrims.setRange(1, 50)
        self.total_pilgrims.valueChanged.connect(self._recalc_total)
        
        step2_layout.addWidget(QLabel("Select Room Type *:"), 0, 0)
        step2_layout.addWidget(self.pricing_opts_cb, 0, 1, 1, 3)
        step2_layout.addWidget(QLabel("Departure Date:"), 1, 0)
        step2_layout.addWidget(self.dep_date, 1, 1)
        step2_layout.addWidget(QLabel("Total Pilgrims:"), 1, 2)
        step2_layout.addWidget(self.total_pilgrims, 1, 3)
        
        main_layout.addWidget(step2_group)
        
        # Step 3: Supplements & Airfare
        step3_group = QGroupBox("3. Supplements & Airfare")
        step3_group.setMaximumWidth(600)
        step3_layout = QGridLayout(step3_group)
        step3_layout.setSpacing(15)
        
        self.airfare_input = QLineEdit("0")
        self.airfare_input.textChanged.connect(self._recalc_total)
        
        self.supplements_table = QTableWidget(0, 2)
        self.supplements_table.setHorizontalHeaderLabels(["Supplement Description", "Cost"])
        self.supplements_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.supplements_table.itemChanged.connect(self._recalc_total)
        self.supplements_table.setMinimumHeight(150)
        
        btn_add_supp = QPushButton("Add Supplement Row")
        btn_add_supp.clicked.connect(self._add_supp_row)
        
        step3_layout.addWidget(QLabel("Airfare (Per Person):"), 0, 0)
        step3_layout.addWidget(self.airfare_input, 0, 1)
        step3_layout.addWidget(btn_add_supp, 1, 0, 1, 2)
        step3_layout.addWidget(self.supplements_table, 2, 0, 1, 2)
        
        main_layout.addWidget(step3_group)
        
        # Step 4: Final Calculation
        step4_group = QGroupBox("4. Financials")
        step4_group.setMaximumWidth(600)
        step4_layout = QFormLayout(step4_group)
        step4_layout.setSpacing(15)
        
        self.calc_total = QLineEdit("0")
        self.calc_total.setReadOnly(True)
        self.calc_total.setStyleSheet("font-weight: bold; color: #10B981; font-size: 16px;")
        
        self.amount_paid = QLineEdit("0")
        
        self.status_cb = QComboBox()
        self.status_cb.addItems(["Draft", "Confirmed", "Paid", "Cancelled"])
        
        step4_layout.addRow("Calculated Total:", self.calc_total)
        step4_layout.addRow("Amount Paid:", self.amount_paid)
        step4_layout.addRow("Booking Status:", self.status_cb)
        
        main_layout.addWidget(step4_group)
        
        # Footer
        footer = QHBoxLayout()
        self.btn_cancel = QPushButton("Cancel")
        self.btn_save = QPushButton("Save Custom Booking")
        self.btn_save.setObjectName("btn_primary")
        self.btn_save.setShortcut("Return")
        
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self._on_save)
        
        footer.addStretch()
        footer.addWidget(self.btn_cancel)
        footer.addWidget(self.btn_save)
        main_layout.addLayout(footer)

    def _on_form_data_loaded(self, result):
        self.customer_cb.clear()
        self.template_cb.clear()
        
        customers = result.get('customers', [])
        templates = result.get('templates', [])
        
        self.customer_map = {c.full_name: c.id for c in customers}
        self.customer_cb.addItems(["-- Select Customer --"] + list(self.customer_map.keys()))
        
        self.template_map = {t.name: t.id for t in templates}
        self.template_nights = {t.id: t.total_nights for t in templates}
        self.template_cb.addItems(["-- Select Template --"] + list(self.template_map.keys()))

    def _on_template_selected(self):
        t_name = self.template_cb.currentText()
        if t_name in self.template_map:
            t_id = self.template_map[t_name]
            self.viewmodel.load_template_pricing(t_id)

    def _on_pricing_loaded(self, pricing_list):
        self.pricing_opts_cb.blockSignals(True)
        self.pricing_opts_cb.clear()
        self.template_pricing_cache = pricing_list
        for p in pricing_list:
            label = f"{p.room_type} | Base PKR {float(p.price_per_person):,.0f}"
            self.pricing_opts_cb.addItem(label, p)
        self.pricing_opts_cb.blockSignals(False)
        self._recalc_total()

    def _add_supp_row(self):
        row = self.supplements_table.rowCount()
        self.supplements_table.insertRow(row)
        self.supplements_table.setItem(row, 0, QTableWidgetItem("Haramain Train VIP"))
        self.supplements_table.setItem(row, 1, QTableWidgetItem("315"))

    def _recalc_total(self, *args):
        try:
            idx = self.pricing_opts_cb.currentIndex()
            if idx < 0:
                base_pkg_price = 0
            else:
                p = self.pricing_opts_cb.itemData(idx)
                base_pkg_price = float(p.price_per_person)
            
            pilgrims = self.total_pilgrims.value()
            airfare = float(self.airfare_input.text() or 0)
            
            supp_total = 0
            for i in range(self.supplements_table.rowCount()):
                cost_item = self.supplements_table.item(i, 1)
                if cost_item:
                    try:
                        supp_total += float(cost_item.text() or 0)
                    except ValueError:
                        pass
            
            grand_total = ((base_pkg_price + airfare) * pilgrims) + supp_total
            self.calc_total.setText(f"{grand_total:,.2f}")
        except Exception:
            pass

    def _on_save(self):
        c_name = self.customer_cb.currentText()
        if c_name not in self.customer_map:
            QMessageBox.warning(self, "Validation", "Please select a valid customer.")
            return
            
        idx = self.pricing_opts_cb.currentIndex()
        if idx < 0:
            QMessageBox.warning(self, "Validation", "Please select a room tier.")
            return
            
        pricing_data = self.pricing_opts_cb.itemData(idx)
        t_name = self.template_cb.currentText()
        t_id = self.template_map.get(t_name, None)
        total_nights = self.template_nights.get(t_id, 0)
        
        supplements_dict = {}
        for i in range(self.supplements_table.rowCount()):
            desc = self.supplements_table.item(i, 0).text().strip() if self.supplements_table.item(i, 0) else ""
            cost = self.supplements_table.item(i, 1).text().strip() if self.supplements_table.item(i, 1) else "0"
            if desc:
                supplements_dict[desc] = float(cost or 0)
                
        # Parse total from string formatting
        total_str = self.calc_total.text().replace(',', '')
        
        booking_data = {
            'customer_id': self.customer_map[c_name],
            'template_id': t_id,
            'booking_date': self.bkg_date.date().toPython(),
            'departure_date': self.dep_date.date().toPython(),
            'room_type': pricing_data.room_type,
            'total_nights': total_nights, 
            'total_pilgrims': self.total_pilgrims.value(),
            'base_package_price': float(pricing_data.price_per_person),
            'airfare_price': float(self.airfare_input.text() or 0),
            'amount_paid': float(self.amount_paid.text() or 0),
            'supplements': supplements_dict,
            'status': self.status_cb.currentText()
        }
        
        self.btn_save.setEnabled(False)
        self.viewmodel.save_booking(booking_data, [], self.current_user_id)

    def _on_saved(self, result):
        self.accept()

    def _on_error(self, message):
        self.btn_save.setEnabled(True)
        QMessageBox.critical(self, "Error", message)
