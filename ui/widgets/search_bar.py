from PySide6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton
from PySide6.QtCore import Signal

class SearchBar(QWidget):
    search_requested = Signal(str)

    def __init__(self, placeholder="Search...", parent=None):
        super().__init__(parent)
        self.placeholder = placeholder
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.placeholder)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 14px;
            }
        """)
        self.search_input.returnPressed.connect(self.emit_search)
        
        self.search_btn = QPushButton("Search")
        self.search_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.search_btn.clicked.connect(self.emit_search)

        layout.addWidget(self.search_input)
        layout.addWidget(self.search_btn)

    def emit_search(self):
        query = self.search_input.text().strip()
        self.search_requested.emit(query)
        
    def clear_search(self):
        self.search_input.clear()
