from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QComboBox, QPushButton, QFormLayout, 
                               QDateEdit, QDoubleSpinBox, QTableWidget, 
                               QHeaderView, QTableWidgetItem, QAbstractItemView,
                               QMessageBox, QScrollArea, QWidget, QAbstractItemView)
from PySide6.QtCore import QDate, Qt

class InvoiceForm(QDialog):
    def __init__(self, viewmodel, current_user_id, parent=None):
        super().__init__(parent)
        self.viewmodel = viewmodel
        self.current_user_id = current_user_id
        self.setWindowTitle("Create New Invoice")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        self._setup_ui()
        self._connect_signals()
        
        # Trigger async load
        self.cmb_customer.addItem("Loading customers...", None)
        self.cmb_customer.setEnabled(False)
        self.viewmodel.load_form_data()
        
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.container = QWidget()
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetMinimumSize)
        
        title = QLabel("New Invoice")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #FFFFFF; margin-bottom: 10px;")
        layout.addWidget(title)
        
        form_layout = QHBoxLayout()
        
        # Left side: basic details
        left_form = QFormLayout()
        left_form.setSpacing(15)
        self.cmb_customer = QComboBox()
        self.txt_group_code = QLineEdit()
        self.txt_group_code.setPlaceholderText("e.g. 480900317975")
        self.dt_issue = QDateEdit(QDate.currentDate())
        self.dt_issue.setCalendarPopup(True)
        self.dt_due = QDateEdit(QDate.currentDate().addDays(7))
        self.dt_due.setCalendarPopup(True)
        
        left_form.addRow("Customer:", self.cmb_customer)
        left_form.addRow("Group Code:", self.txt_group_code)
        left_form.addRow("Issue Date:", self.dt_issue)
        left_form.addRow("Due Date:", self.dt_due)
        form_layout.addLayout(left_form)
        
        layout.addLayout(form_layout)
        
        # Items Table
        lbl_items = QLabel("Invoice Items")
        lbl_items.setStyleSheet("font-weight: bold; margin-top: 15px; font-size: 14px; color: #818CF8;")
        layout.addWidget(lbl_items)
        
        self.tbl_items = QTableWidget(0, 5)
        self.tbl_items.setHorizontalHeaderLabels(["Passenger Name", "Passport", "Details", "Amount", "Actions"])
        self.tbl_items.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tbl_items.setMinimumHeight(250)
        layout.addWidget(self.tbl_items)
        
        btn_add_item = QPushButton("+ Add Passenger/Item")
        btn_add_item.setStyleSheet("padding: 8px 16px; margin-bottom: 10px;")
        btn_add_item.clicked.connect(self._add_item_row)
        layout.addWidget(btn_add_item, alignment=Qt.AlignmentFlag.AlignLeft)
        
        # Automatically add one row
        self._add_item_row()
        
        # Totals section
        totals_layout = QFormLayout()
        totals_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.lbl_subtotal = QLabel("Rs. 0.00")
        
        self.sp_tax = QDoubleSpinBox()
        self.sp_tax.setRange(0, 999999999)
        self.sp_tax.setPrefix("Rs. ")
        self.sp_tax.valueChanged.connect(self._calculate_total)
        
        self.lbl_total = QLabel("Rs. 0.00")
        self.lbl_total.setStyleSheet("font-weight: bold; font-size: 16px; color: #10B981;")
        
        totals_layout.addRow("Subtotal:", self.lbl_subtotal)
        totals_layout.addRow("Tax Amount:", self.sp_tax)
        totals_layout.addRow("Grand Total:", self.lbl_total)
        
        layout.addLayout(totals_layout)
        
        self.scroll.setWidget(self.container)
        main_layout.addWidget(self.scroll)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Save Invoice")
        btn_save.setObjectName("btn_primary")
        btn_save.setShortcut("Return")
        btn_cancel = QPushButton("Cancel")
        
        btn_save.clicked.connect(self._save)
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        main_layout.addLayout(btn_layout)
        
    def _connect_signals(self):
        self.viewmodel.form_data_loaded.connect(self._on_customers_loaded)
        
    def _on_customers_loaded(self, customers):
        self.cmb_customer.clear()
        self.cmb_customer.addItem("-- Select Customer --", None)
        for c in customers:
            self.cmb_customer.addItem(c.full_name, c.id)
        self.cmb_customer.setEnabled(True)
        
    def _add_item_row(self):
        row = self.tbl_items.rowCount()
        self.tbl_items.insertRow(row)
        
        txt_name = QLineEdit()
        txt_passport = QLineEdit()
        txt_details = QLineEdit()
        sp_amount = QDoubleSpinBox()
        sp_amount.setRange(0, 999999999)
        sp_amount.valueChanged.connect(self._calculate_total)
        
        btn_remove = QPushButton("❌")
        btn_remove.setStyleSheet("color: #EF4444; background: transparent; border: none; font-size: 16px;")
        btn_remove.clicked.connect(lambda: self._remove_item_row(btn_remove))
        
        self.tbl_items.setCellWidget(row, 0, txt_name)
        self.tbl_items.setCellWidget(row, 1, txt_passport)
        self.tbl_items.setCellWidget(row, 2, txt_details)
        self.tbl_items.setCellWidget(row, 3, sp_amount)
        self.tbl_items.setCellWidget(row, 4, btn_remove)
        
    def _remove_item_row(self, button):
        for i in range(self.tbl_items.rowCount()):
            if self.tbl_items.cellWidget(i, 4) == button:
                self.tbl_items.removeRow(i)
                self._calculate_total()
                break
                
    def _calculate_total(self):
        subtotal = 0.0
        for i in range(self.tbl_items.rowCount()):
            sp_amount = self.tbl_items.cellWidget(i, 3)
            if sp_amount:
                subtotal += sp_amount.value()
                
        self.lbl_subtotal.setText(f"Rs. {subtotal:,.2f}")
        
        total = subtotal + self.sp_tax.value()
        self.lbl_total.setText(f"Rs. {total:,.2f}")
        
    def _save(self):
        customer_id = self.cmb_customer.currentData()
        if not customer_id:
            QMessageBox.warning(self, "Validation Error", "Please select a customer.")
            return
            
        if self.tbl_items.rowCount() == 0:
            QMessageBox.warning(self, "Validation Error", "Please add at least one item to the invoice.")
            return
            
        # Calculate subtotal manually
        subtotal = 0.0
        items_data = []
        for i in range(self.tbl_items.rowCount()):
            name = self.tbl_items.cellWidget(i, 0).text()
            passport = self.tbl_items.cellWidget(i, 1).text()
            details = self.tbl_items.cellWidget(i, 2).text()
            amount = self.tbl_items.cellWidget(i, 3).value()
            
            if not details and amount == 0:
                continue # Skip empty rows
                
            subtotal += amount
            items_data.append({
                "description": details or "Travel Services",
                "passenger_name": name or None,
                "passport_number": passport or None,
                "quantity": 1,
                "unit_price": amount,
                "total_price": amount
            })
            
        if not items_data:
            QMessageBox.warning(self, "Validation Error", "Please enter valid item details.")
            return
            
        tax = self.sp_tax.value()
        total = subtotal + tax
            
        invoice_data = {
            "customer_id": customer_id,
            "group_code": self.txt_group_code.text() or None,
            "issue_date": self.dt_issue.date().toPython(),
            "due_date": self.dt_due.date().toPython(),
            "subtotal": subtotal,
            "tax_amount": tax,
            "total_amount": total,
            "amount_remaining": total,
            "status": "Unpaid"
        }
        
        self.viewmodel.create_invoice(invoice_data, items_data, self.current_user_id)
        self.accept()
