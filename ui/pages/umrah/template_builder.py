import json
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QLineEdit, QFormLayout, QComboBox, 
                               QMessageBox, QGroupBox, QGridLayout, QTextEdit,
                               QTableWidget, QTableWidgetItem, QHeaderView, QDoubleSpinBox, QSpinBox)
from PySide6.QtCore import Qt
from viewmodels.umrah_viewmodel import UmrahViewModel

class TemplateBuilderDialog(QDialog):
    def __init__(self, current_user_id="system", parent=None):
        super().__init__(parent)
        self.current_user_id = current_user_id
        self.template_id = None
        self.viewmodel = UmrahViewModel()
        self.viewmodel.template_saved.connect(self._on_saved)
        self.viewmodel.error_occurred.connect(self._on_error)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Umrah Master Template Builder")
        self.setMinimumSize(800, 600)
        
        main_layout = QVBoxLayout(self)
        
        # Base Details
        base_group = QGroupBox("Template Basics")
        base_layout = QGridLayout(base_group)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. 14 Nights Premium")
        self.star_rating = QDoubleSpinBox()
        self.star_rating.setRange(1.0, 5.0)
        self.star_rating.setSingleStep(0.5)
        self.star_rating.setValue(3.0)
        
        self.currency_cb = QComboBox()
        self.currency_cb.addItems(["PKR", "SAR"])
        
        self.total_nights = QSpinBox()
        self.total_nights.setRange(1, 60)
        self.total_days = QSpinBox()
        self.total_days.setRange(1, 60)
        
        base_layout.addWidget(QLabel("Template Name *:"), 0, 0)
        base_layout.addWidget(self.name_input, 0, 1, 1, 3)
        base_layout.addWidget(QLabel("Star Rating:"), 1, 0)
        base_layout.addWidget(self.star_rating, 1, 1)
        base_layout.addWidget(QLabel("Currency:"), 1, 2)
        base_layout.addWidget(self.currency_cb, 1, 3)
        base_layout.addWidget(QLabel("Total Nights:"), 2, 0)
        base_layout.addWidget(self.total_nights, 2, 1)
        base_layout.addWidget(QLabel("Total Days:"), 2, 2)
        base_layout.addWidget(self.total_days, 2, 3)
        
        main_layout.addWidget(base_group)
        
        # Hotels
        hotels_group = QGroupBox("Hotels & Inclusions")
        hotels_layout = QGridLayout(hotels_group)
        
        self.mak_hotel = QLineEdit()
        self.mak_nights = QSpinBox()
        self.med_hotel = QLineEdit()
        self.med_nights = QSpinBox()
        self.meal_plan = QLineEdit()
        self.inclusions = QTextEdit()
        self.inclusions.setPlaceholderText("Enter inclusions as JSON or plain text...")
        self.inclusions.setMaximumHeight(60)
        
        hotels_layout.addWidget(QLabel("Makkah Hotel:"), 0, 0)
        hotels_layout.addWidget(self.mak_hotel, 0, 1)
        hotels_layout.addWidget(QLabel("Makkah Nights:"), 0, 2)
        hotels_layout.addWidget(self.mak_nights, 0, 3)
        
        hotels_layout.addWidget(QLabel("Medinah Hotel:"), 1, 0)
        hotels_layout.addWidget(self.med_hotel, 1, 1)
        hotels_layout.addWidget(QLabel("Medinah Nights:"), 1, 2)
        hotels_layout.addWidget(self.med_nights, 1, 3)
        
        hotels_layout.addWidget(QLabel("Meal Plan:"), 2, 0)
        hotels_layout.addWidget(self.meal_plan, 2, 1, 1, 3)
        
        hotels_layout.addWidget(QLabel("Inclusions:"), 3, 0)
        hotels_layout.addWidget(self.inclusions, 3, 1, 1, 3)
        
        main_layout.addWidget(hotels_group)
        
        # Pricing Matrix
        pricing_group = QGroupBox("Pricing Matrix")
        pricing_layout = QVBoxLayout(pricing_group)
        
        btn_add_row = QPushButton("Add Pricing Row")
        btn_add_row.clicked.connect(self._add_pricing_row)
        pricing_layout.addWidget(btn_add_row, alignment=Qt.AlignmentFlag.AlignLeft)
        
        self.pricing_table = QTableWidget(0, 2)
        self.pricing_table.setHorizontalHeaderLabels(["Room Type", "Price Per Person"])
        self.pricing_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        pricing_layout.addWidget(self.pricing_table)
        
        main_layout.addWidget(pricing_group)
        
        # Footer
        footer = QHBoxLayout()
        self.btn_cancel = QPushButton("Cancel")
        self.btn_save = QPushButton("Save Template")
        self.btn_save.setShortcut("Return")
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self._on_save)
        footer.addStretch()
        footer.addWidget(self.btn_cancel)
        footer.addWidget(self.btn_save)
        main_layout.addLayout(footer)

    def load_template(self, template, pricing_list):
        self.template_id = template.id
        self.setWindowTitle("Edit Umrah Master Template")
        self.name_input.setText(template.name)
        self.star_rating.setValue(float(template.star_rating or 3.0))
        self.currency_cb.setCurrentText(template.currency)
        self.total_nights.setValue(template.total_nights or 0)
        self.total_days.setValue(template.total_days or 0)
        
        self.mak_hotel.setText(template.makkah_hotel or "")
        self.mak_nights.setValue(template.makkah_nights or 0)
        self.med_hotel.setText(template.medinah_hotel or "")
        self.med_nights.setValue(template.medinah_nights or 0)
        self.meal_plan.setText(template.meal_plan or "")
        
        if template.inclusions and isinstance(template.inclusions, dict):
            self.inclusions.setPlainText(template.inclusions.get("details", ""))
            
        self.pricing_table.setRowCount(0)
        for pricing in pricing_list:
            row = self.pricing_table.rowCount()
            self.pricing_table.insertRow(row)
            self.pricing_table.setItem(row, 0, QTableWidgetItem(pricing.room_type))
            self.pricing_table.setItem(row, 1, QTableWidgetItem(str(pricing.price_per_person)))

    def _add_pricing_row(self):
        row = self.pricing_table.rowCount()
        self.pricing_table.insertRow(row)
        self.pricing_table.setItem(row, 0, QTableWidgetItem("Double"))
        self.pricing_table.setItem(row, 1, QTableWidgetItem("0"))

    def _on_save(self):
        name = self.name_input.text().strip()
        mak_hotel = self.mak_hotel.text().strip()
        med_hotel = self.med_hotel.text().strip()
        
        # Validation checks
        if not name:
            QMessageBox.warning(self, "Validation Error", "Template Name is required.")
            return
            
        if self.total_nights.value() <= 0 or self.total_days.value() <= 0:
            QMessageBox.warning(self, "Validation Error", "Total Nights and Total Days must be greater than 0.")
            return
            
        if not mak_hotel and not med_hotel:
            QMessageBox.warning(self, "Validation Error", "At least one hotel (Makkah or Medinah) must be provided.")
            return

        template_data = {
            'name': name,
            'star_rating': self.star_rating.value(),
            'currency': self.currency_cb.currentText(),
            'total_nights': self.total_nights.value(),
            'total_days': self.total_days.value(),
            'makkah_hotel': self.mak_hotel.text().strip(),
            'makkah_nights': self.mak_nights.value(),
            'medinah_hotel': self.med_hotel.text().strip(),
            'medinah_nights': self.med_nights.value(),
            'meal_plan': self.meal_plan.text().strip(),
            'inclusions': {'details': self.inclusions.toPlainText().strip()}
        }
        if self.template_id:
            template_data['id'] = self.template_id
        
        pricing_matrix = []
        for i in range(self.pricing_table.rowCount()):
            try:
                rt = self.pricing_table.item(i, 0).text().strip()
                price = float(self.pricing_table.item(i, 1).text() or 0)
                
                if rt:
                    pricing_matrix.append({
                        'room_type': rt,
                        'price_per_person': price
                    })
            except Exception as e:
                pass # skip invalid rows
                
        if not pricing_matrix:
            QMessageBox.warning(self, "Error", "Add at least one valid pricing row.")
            return

        self.btn_save.setEnabled(False)
        self.viewmodel.save_template(template_data, pricing_matrix, self.current_user_id)

    def _on_saved(self, result):
        self.accept()

    def _on_error(self, message):
        self.btn_save.setEnabled(True)
        QMessageBox.critical(self, "Error", message)
