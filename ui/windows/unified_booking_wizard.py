from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QPushButton, QScrollArea, QTabWidget)
from PySide6.QtCore import Qt
from ui.widgets.pax_widget import PaxWidget
from ui.components.searchable_combo_box import SearchableComboBox

class ServiceLegWidget(QWidget):
    def __init__(self, service_type="Hotel", parent=None):
        super().__init__(parent)
        self.service_type = service_type
        
        layout = QHBoxLayout(self)
        layout.addWidget(QLabel(f"{self.service_type} Vendor:"))
        
        self.vendor_dropdown = SearchableComboBox()
        self.vendor_dropdown.search_input.setPlaceholderText(f"Search {self.service_type} vendors...")
        
        # This would be populated with real data from the DB later
        # Example: self.vendor_dropdown.set_data([(v.company_name, v.id) for v in vendors])
        
        layout.addWidget(self.vendor_dropdown)
        layout.addStretch()


class UnifiedBookingWizard(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Unified Booking Wizard")
        self.resize(800, 600)
        self.setup_ui()
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Tabs for different sections
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # --- Pax Tab ---
        self.pax_tab = QWidget()
        self.pax_layout = QVBoxLayout(self.pax_tab)
        
        # Scroll area for Pax widgets
        self.pax_scroll = QScrollArea()
        self.pax_scroll.setWidgetResizable(True)
        self.pax_container = QWidget()
        self.pax_container_layout = QVBoxLayout(self.pax_container)
        self.pax_container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.pax_scroll.setWidget(self.pax_container)
        
        # Buttons for PAX management
        pax_btn_layout = QHBoxLayout()
        add_pax_btn = QPushButton("+ Add Passenger")
        add_pax_btn.clicked.connect(self.add_pax_widget)
        pax_btn_layout.addWidget(add_pax_btn)
        pax_btn_layout.addStretch()
        
        self.pax_layout.addWidget(self.pax_scroll)
        self.pax_layout.addLayout(pax_btn_layout)
        
        self.tabs.addTab(self.pax_tab, "Passengers (PAX)")
        
        # Add the first default Pax Widget
        self.add_pax_widget()
        
        # --- Services Tab ---
        self.services_tab = QWidget()
        self.services_layout = QVBoxLayout(self.services_tab)
        
        self.hotel_leg = ServiceLegWidget("Hotel")
        self.transport_leg = ServiceLegWidget("Transport")
        
        self.services_layout.addWidget(self.hotel_leg)
        self.services_layout.addWidget(self.transport_leg)
        self.services_layout.addStretch()
        
        self.tabs.addTab(self.services_tab, "Services & Vendors")

    def add_pax_widget(self):
        pax_widget = PaxWidget()
        self.pax_container_layout.addWidget(pax_widget)
