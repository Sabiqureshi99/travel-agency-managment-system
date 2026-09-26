from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QComboBox, QPushButton, QFormLayout, 
                               QDateEdit, QSpinBox)
from PySide6.QtCore import QDate

class HajjGroupForm(QDialog):
    def __init__(self, viewmodel, current_user_id, parent=None):
        super().__init__(parent)
        self.viewmodel = viewmodel
        self.current_user_id = current_user_id
        self.setWindowTitle("Add/Edit Hajj Group")
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.group_name = QLineEdit()
        self.year = QSpinBox()
        self.year.setRange(2024, 2030)
        self.application_type = QComboBox()
        self.application_type.addItems(["Private", "Government"])
        self.total_quota = QSpinBox()
        self.total_quota.setRange(1, 1000)
        self.package_price = QLineEdit()
        self.departure_date = QDateEdit(QDate.currentDate())
        self.return_date = QDateEdit(QDate.currentDate().addDays(30))
        self.makkah_hotel = QLineEdit()
        self.madinah_hotel = QLineEdit()
        self.status = QComboBox()
        self.status.addItems(["Open", "Full", "Closed"])
        
        form.addRow("Group Name:", self.group_name)
        form.addRow("Year:", self.year)
        form.addRow("Application Type:", self.application_type)
        form.addRow("Total Quota:", self.total_quota)
        form.addRow("Package Price:", self.package_price)
        form.addRow("Departure Date:", self.departure_date)
        form.addRow("Return Date:", self.return_date)
        form.addRow("Makkah Hotel:", self.makkah_hotel)
        form.addRow("Madinah Hotel:", self.madinah_hotel)
        form.addRow("Status:", self.status)
        
        layout.addLayout(form)
        
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Save")
        btn_save.setShortcut("Return")
        btn_cancel = QPushButton("Cancel")
        btn_save.clicked.connect(self._save)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        
        layout.addLayout(btn_layout)
        
    def _save(self):
        data = {
            "group_name": self.group_name.text(),
            "year": self.year.value(),
            "application_type": self.application_type.currentText(),
            "total_quota": self.total_quota.value(),
            "package_price": float(self.package_price.text() or 0),
            "departure_date": self.departure_date.date().toPython(),
            "return_date": self.return_date.date().toPython(),
            "makkah_hotel": self.makkah_hotel.text(),
            "madinah_hotel": self.madinah_hotel.text(),
            "status": self.status.currentText()
        }
        self.viewmodel.save_group(data, self.current_user_id)
        self.accept()
