import logging
from datetime import date
from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QAbstractItemView,
    QWidget, QScrollArea, QDoubleSpinBox, QSpinBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from config.database import get_session
from models.quotation import Quotation, QuotationItem
from core.base_model import generate_uuid

logger = logging.getLogger(__name__)

class QuotationBuilderDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Quotation / Estimate")
        self.setMinimumSize(900, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: #1E1E2E;
                color: #FFFFFF;
            }
            QLabel {
                color: #FFFFFF;
                font-size: 14px;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox {
                background-color: #252836;
                color: #FFFFFF;
                border: 1px solid #3A3D4E;
                padding: 6px;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #2563EB;
                color: #FFFFFF;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1D4ED8;
            }
            QTableWidget {
                background-color: #252836;
                color: #FFFFFF;
                border: 1px solid #3A3D4E;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #1E1E2E;
                color: #8892B0;
                padding: 4px;
                border: none;
            }
            .total-label {
                font-size: 20px;
                font-weight: bold;
                color: #10B981;
            }
        """)

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(20)

        # 1. Walk-in Details Section
        details_layout = QHBoxLayout()
        
        self.txt_guest_name = QLineEdit()
        self.txt_guest_name.setPlaceholderText("Guest / Walk-in Name")
        
        self.txt_guest_phone = QLineEdit()
        self.txt_guest_phone.setPlaceholderText("Phone Number")
        
        details_layout.addWidget(QLabel("Guest Name:"))
        details_layout.addWidget(self.txt_guest_name)
        details_layout.addWidget(QLabel("Phone:"))
        details_layout.addWidget(self.txt_guest_phone)
        details_layout.addStretch()
        
        self.layout.addLayout(details_layout)

        # 2. Dynamic Services List (Using QTableWidget for ease of entry)
        self.tbl_services = QTableWidget(0, 5)
        self.tbl_services.setHorizontalHeaderLabels(["Description", "Qty", "Unit Price", "Total", "Action"])
        self.tbl_services.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tbl_services.setColumnWidth(1, 80)
        self.tbl_services.setColumnWidth(2, 130)
        self.tbl_services.setColumnWidth(3, 130)
        self.tbl_services.setColumnWidth(4, 60)
        
        # UI Fixes for Table
        self.tbl_services.verticalHeader().setVisible(False)
        self.tbl_services.verticalHeader().setDefaultSectionSize(45)
        self.tbl_services.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.tbl_services.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        self.layout.addWidget(self.tbl_services)

        # Controls for adding lines
        controls_layout = QHBoxLayout()
        self.btn_add_line = QPushButton("+ Add Service")
        self.btn_add_line.setStyleSheet("background-color: #059669; color: white;")
        self.btn_add_line.clicked.connect(self.add_service_line)
        controls_layout.addWidget(self.btn_add_line)
        controls_layout.addStretch()
        
        self.layout.addLayout(controls_layout)

        # 3. Grand Total and Actions
        footer_layout = QHBoxLayout()
        
        self.lbl_grand_total = QLabel("Grand Total: 0.00")
        self.lbl_grand_total.setProperty("class", "total-label")
        self.lbl_grand_total.setStyleSheet("font-size: 20px; font-weight: bold; color: #10B981;")
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setStyleSheet("background-color: #EF4444;")
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_save = QPushButton("Save Quotation")
        self.btn_save.clicked.connect(self.save_quotation)
        
        footer_layout.addWidget(self.lbl_grand_total)
        footer_layout.addStretch()
        footer_layout.addWidget(self.btn_cancel)
        footer_layout.addWidget(self.btn_save)
        
        self.layout.addLayout(footer_layout)

        # Add initial blank line
        self.add_service_line()

    def add_service_line(self):
        row = self.tbl_services.rowCount()
        self.tbl_services.insertRow(row)
        
        # Description
        txt_desc = QLineEdit()
        txt_desc.setPlaceholderText("e.g. Flight to Dubai")
        
        # Qty
        spn_qty = QSpinBox()
        spn_qty.setMinimum(1)
        spn_qty.setMaximum(999)
        spn_qty.setValue(1)
        spn_qty.valueChanged.connect(self.calculate_totals)
        
        # Unit Price
        spn_price = QDoubleSpinBox()
        spn_price.setMinimum(0)
        spn_price.setMaximum(9999999)
        spn_price.setValue(0.0)
        spn_price.setDecimals(2)
        spn_price.valueChanged.connect(self.calculate_totals)
        
        # Line Total
        lbl_total = QLabel("0.00")
        lbl_total.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        # Delete Button
        btn_delete = QPushButton("X")
        btn_delete.setFixedSize(30, 30)
        btn_delete.setStyleSheet("background-color: #EF4444; border-radius: 4px; font-weight: bold; font-size: 14px;")
        btn_delete.clicked.connect(lambda: self.remove_service_line(txt_desc))
        
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.addWidget(btn_delete, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.tbl_services.setCellWidget(row, 0, txt_desc)
        self.tbl_services.setCellWidget(row, 1, spn_qty)
        self.tbl_services.setCellWidget(row, 2, spn_price)
        self.tbl_services.setCellWidget(row, 3, lbl_total)
        self.tbl_services.setCellWidget(row, 4, btn_container)

    def remove_service_line(self, widget):
        for row in range(self.tbl_services.rowCount()):
            if self.tbl_services.cellWidget(row, 0) == widget:
                self.tbl_services.removeRow(row)
                self.calculate_totals()
                break

    def calculate_totals(self):
        grand_total = 0.0
        for row in range(self.tbl_services.rowCount()):
            qty_widget = self.tbl_services.cellWidget(row, 1)
            price_widget = self.tbl_services.cellWidget(row, 2)
            total_label = self.tbl_services.cellWidget(row, 3)
            
            if qty_widget and price_widget and total_label:
                line_total = qty_widget.value() * price_widget.value()
                total_label.setText(f"{line_total:.2f}")
                grand_total += line_total
                
        self.lbl_grand_total.setText(f"Grand Total: {grand_total:,.2f}")
        return grand_total

    def save_quotation(self):
        guest_name = self.txt_guest_name.text().strip()
        
        if not guest_name:
            QMessageBox.warning(self, "Validation Error", "Please provide a guest/walk-in name.")
            return
            
        grand_total = self.calculate_totals()
        if grand_total < 0:
            QMessageBox.warning(self, "Validation Error", "Total amount cannot be negative.")
            return
            
        items_data = []
        for row in range(self.tbl_services.rowCount()):
            desc = self.tbl_services.cellWidget(row, 0).text().strip()
            qty = self.tbl_services.cellWidget(row, 1).value()
            price = self.tbl_services.cellWidget(row, 2).value()
            line_total = qty * price
            
            if desc:
                items_data.append({
                    "description": desc,
                    "qty": qty,
                    "price": price,
                    "total": line_total
                })
                
        if not items_data:
            QMessageBox.warning(self, "Validation Error", "Please add at least one valid service line.")
            return
            
        try:
            with get_session() as session:
                new_quote = Quotation(
                    id=generate_uuid(),
                    guest_name=guest_name,
                    guest_phone=self.txt_guest_phone.text().strip(),
                    total_amount=grand_total,
                    status="Pending"
                )
                session.add(new_quote)
                
                for item in items_data:
                    q_item = QuotationItem(
                        id=generate_uuid(),
                        quotation_id=new_quote.id,
                        service_description=item["description"],
                        qty=item["qty"],
                        unit_price=item["price"],
                        total=item["total"]
                    )
                    session.add(q_item)
                    
                session.commit()
                QMessageBox.information(self, "Success", "Quotation saved successfully!")
                self.accept()
                
        except Exception as e:
            logger.exception("Failed to save quotation")
            QMessageBox.critical(self, "Error", f"Could not save quotation: {str(e)}")
