from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt, Signal

class TopBar(QWidget):
    logout_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setFixedHeight(60)
        self.setStyleSheet("background-color: #ecf0f1; border-bottom: 1px solid #bdc3c7;")
        layout = QHBoxLayout(self)
        
        self.title_label = QLabel("Dashboard")
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50; border: none;")
        layout.addWidget(self.title_label)
        
        layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Minimum))
        
        self.user_label = QLabel("Welcome, Admin")
        self.user_label.setStyleSheet("font-size: 14px; color: #2c3e50; border: none;")
        layout.addWidget(self.user_label)
        
        self.logout_btn = QPushButton("Logout")
        self.logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.logout_btn.clicked.connect(self.logout_requested.emit)
        layout.addWidget(self.logout_btn)

    def set_title(self, title):
        self.title_label.setText(title)
