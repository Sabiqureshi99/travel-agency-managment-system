from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QFrame, QApplication
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QRect, QPoint

class ToastNotification(QFrame):
    def __init__(self, message, type="info", duration=3000, parent=None):
        super().__init__(parent)
        # If parent is None, it acts as a top-level window
        if parent is None:
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.layout = QHBoxLayout(self)
        self.label = QLabel(message)
        self.layout.addWidget(self.label)
        
        colors = {
            "info": "#2196F3",
            "success": "#4CAF50",
            "warning": "#FFC107",
            "error": "#F44336"
        }
        bg_color = colors.get(type, "#333333")
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                color: white;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
            }}
        """)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.fade_out)
        self.timer.start(duration)
        
        self.setWindowOpacity(0.0)
        self.fade_in()

    def fade_in(self):
        self.anim_in = QPropertyAnimation(self, b"windowOpacity")
        self.anim_in.setDuration(300)
        self.anim_in.setStartValue(0.0)
        self.anim_in.setEndValue(0.95)
        self.anim_in.start()

    def fade_out(self):
        self.anim_out = QPropertyAnimation(self, b"windowOpacity")
        self.anim_out.setDuration(500)
        self.anim_out.setStartValue(0.95)
        self.anim_out.setEndValue(0.0)
        self.anim_out.finished.connect(self.close)
        self.anim_out.start()

class NotificationCenter:
    @staticmethod
    def show(message, type="info", duration=3000, parent=None):
        toast = ToastNotification(message, type, duration, parent)
        if parent:
            # Center it at the bottom of the parent
            x = (parent.width() - toast.sizeHint().width()) // 2
            y = parent.height() - toast.sizeHint().height() - 20
            toast.move(x, y)
        else:
            screen = QApplication.primaryScreen().availableGeometry()
            x = screen.width() - toast.sizeHint().width() - 20
            y = screen.height() - toast.sizeHint().height() - 20
            toast.move(x, y)
        toast.show()
        return toast
