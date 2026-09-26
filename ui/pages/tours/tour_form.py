from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QComboBox, QPushButton, QFormLayout, 
                               QDateEdit, QDoubleSpinBox, QSpinBox)
from PySide6.QtCore import Qt, QDate

class TourForm(QDialog):
    def __init__(self, item=None, parent=None):
        super().__init__(parent)
        self.item = item
        self.setWindowTitle("Add/Edit Tour Package")
        self.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.tour_name = QLineEdit()
        self.destination = QLineEdit()
        self.start_date = QDateEdit(QDate.currentDate())
        self.start_date.setCalendarPopup(True)
        self.end_date = QDateEdit(QDate.currentDate().addDays(5))
        self.end_date.setCalendarPopup(True)
        self.capacity = QSpinBox()
        self.capacity.setRange(1, 100)
        self.price = QDoubleSpinBox()
        self.price.setRange(0, 10000000)
        self.status = QComboBox()
        self.status.addItems(["Active", "Inactive"])
        
        form.addRow("Tour Name *:", self.tour_name)
        form.addRow("Destination:", self.destination)
        form.addRow("Start Date:", self.start_date)
        form.addRow("End Date:", self.end_date)
        form.addRow("Capacity:", self.capacity)
        form.addRow("Price:", self.price)
        form.addRow("Status:", self.status)
        
        layout.addLayout(form)
        
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Save")
        btn_save.setShortcut("Return")
        btn_cancel = QPushButton("Cancel")
        btn_save.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        
        layout.addLayout(btn_layout)
