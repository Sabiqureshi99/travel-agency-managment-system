from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt

class StatCard(QFrame):
    def __init__(self, title, value, color="#3498db", parent=None):
        super().__init__(parent)
        self.title = title
        self.value = value
        self.color = color
        self.init_ui()

    def init_ui(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(f"""
            StatCard {{
                background-color: white;
                border-radius: 8px;
                border-left: 5px solid {self.color};
                border-top: 1px solid #bdc3c7;
                border-right: 1px solid #bdc3c7;
                border-bottom: 1px solid #bdc3c7;
            }}
        """)
        layout = QVBoxLayout(self)
        
        title_label = QLabel(self.title)
        title_label.setStyleSheet("color: #7f8c8d; font-size: 14px; font-weight: bold; border: none;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        value_label = QLabel(str(self.value))
        value_label.setStyleSheet(f"color: {self.color}; font-size: 24px; font-weight: bold; border: none;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        
    def update_value(self, new_value):
        self.value = new_value
        # Assuming the second widget in the layout is the value label
        self.layout().itemAt(1).widget().setText(str(self.value))
