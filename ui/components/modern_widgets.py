import os
from PySide6.QtWidgets import QFrame, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QGraphicsDropShadowEffect, QWidget
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor

class GlowCard(QFrame):
    """A glassmorphism card with a soft neon glow effect."""
    def __init__(self, parent=None, glow_color="#000000", glow_radius=15, alpha=80):
        super().__init__(parent)
        self.setObjectName("GlowCard")
        
        # Setup shadow effect
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(glow_radius)
        self.shadow.setOffset(0, 4)
        
        color = QColor(glow_color)
        color.setAlpha(alpha)
        self.shadow.setColor(color)
        
        self.setGraphicsEffect(self.shadow)

class GradientButton(QPushButton):
    """A primary button with a gradient background and subtle glow."""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setObjectName("btn_primary")
        
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(15)
        self.shadow.setOffset(0, 4)
        self.shadow.setColor(QColor(221, 36, 118, 100)) # #DD2476 with alpha
        self.setGraphicsEffect(self.shadow)

class KPIDashboardCard(GlowCard):
    """A highly stylized KPI card for the dashboard with a circular icon."""
    def __init__(self, title: str, value: str, icon: str, color_hex: str, parent=None):
        # Pass the specific hex color to the glow card for a customized shadow tint
        super().__init__(parent, glow_color=color_hex, glow_radius=20, alpha=60)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        top_layout = QHBoxLayout()
        
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f"""
            background-color: {color_hex}20; 
            color: {color_hex}; 
            border-radius: 20px; 
            font-size: 20px;
        """)
        icon_lbl.setFixedSize(40, 40)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 13px; color: #8B8B9E; font-weight: 500;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        top_layout.addWidget(icon_lbl)
        top_layout.addWidget(title_label)
        top_layout.addStretch()
        
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("font-size: 32px; font-weight: 700; color: #FFFFFF; margin-top: 10px;")
        
        layout.addLayout(top_layout)
        layout.addWidget(self.value_label)
        
    def set_value(self, value: str):
        self.value_label.setText(value)

class CollapsibleMenu(QWidget):
    """A collapsible menu component for the sidebar."""
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        self.toggle_btn = QPushButton(f"{title}  ▼")
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #8B8B9E;
                text-align: left;
                padding: 12px 20px;
                border: none;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #FFFFFF;
            }
        """)
        self.toggle_btn.clicked.connect(self.toggle)
        
        self.content_frame = QFrame()
        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_layout.setContentsMargins(20, 0, 0, 0) # Indent children
        self.content_layout.setSpacing(2)
        
        self.layout.addWidget(self.toggle_btn)
        self.layout.addWidget(self.content_frame)
        
        self.is_expanded = True

    def add_item(self, button: QPushButton):
        """Add a navigation button to the collapsible frame."""
        button.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #FFFFFF;
                text-align: left;
                padding: 10px 15px;
                border: none;
                border-radius: 6px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background: #1C1C2D;
                border-left: 3px solid #FF512F;
            }
        """)
        self.content_layout.addWidget(button)

    def toggle(self):
        if self.is_expanded:
            self.content_frame.setVisible(False)
            self.toggle_btn.setText(self.toggle_btn.text().replace("▼", "▶"))
            self.is_expanded = False
        else:
            self.content_frame.setVisible(True)
            self.toggle_btn.setText(self.toggle_btn.text().replace("▶", "▼"))
            self.is_expanded = True
