from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                               QLineEdit, QComboBox, QPushButton, QFormLayout, QMessageBox)
from PySide6.QtCore import Qt
from config.database import get_session
from repositories.vendor_repository import VendorRepository
from services.vendor_service import VendorService
from core.enums import VendorType


class VendorForm(QDialog):
    def __init__(self, item=None, parent=None):
        super().__init__(parent)
        self.item = item
        self.setWindowTitle("Add/Edit Vendor")
        self.setMinimumSize(400, 280)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.sup_name = QLineEdit()
        self.sup_type = QComboBox()
        self.sup_type.addItems(["Overall", "Airline", "Hotel", "Transport", "Visa Agent", "Other"])
        self.contact = QLineEdit()
        self.phone = QLineEdit()
        self.email = QLineEdit()

        form.addRow("Vendor Name *:", self.sup_name)
        form.addRow("Vendor Type:", self.sup_type)
        form.addRow("Contact Person:", self.contact)
        form.addRow("Phone:", self.phone)
        form.addRow("Email:", self.email)

        if self.item:
            self.sup_name.setText(self.item.company_name or "")
            if self.item.vendor_type:
                self.sup_type.setCurrentText(self.item.vendor_type)
            self.contact.setText(self.item.contact_person or "")
            self.phone.setText(self.item.phone or "")
            self.email.setText(self.item.email or "")

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Save")
        btn_save.setShortcut("Return")
        btn_cancel = QPushButton("Cancel")
        btn_save.clicked.connect(self._save_vendor)
        btn_cancel.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)

    def _save_vendor(self):
        name = self.sup_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Vendor Name is required.")
            return

        vendor_type_str = self.sup_type.currentText()
        try:
            vendor_type = VendorType(vendor_type_str)
        except ValueError:
            vendor_type = VendorType.OTHER
        contact = self.contact.text().strip()
        phone = self.phone.text().strip()
        email = self.email.text().strip()

        try:
            with get_session() as session:
                repo = VendorRepository(session)
                service = VendorService(repo)
                if self.item:
                    vendor = session.merge(self.item)
                    service.update_vendor(
                        vendor=vendor,
                        name=name,
                        vendor_type=vendor_type,
                        contact_person=contact,
                        phone=phone,
                        email=email
                    )
                else:
                    service.add_vendor(
                        name=name,
                        vendor_type=vendor_type,
                        contact_person=contact,
                        phone=phone,
                        email=email
                    )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save vendor: {e}")
