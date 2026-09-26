from PySide6.QtWidgets import QSplashScreen
from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QPainter, QColor, QFont, QLinearGradient, QPen, QBrush

class SplashScreen(QSplashScreen):
    def __init__(self):
        super().__init__()
        self._status = 'Initialising...'
        self._progress = 0.0
        self._setup_window()
        
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate_progress)
        self._timer.start(30)
    
    def _setup_window(self):
        self.setFixedSize(600, 350)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 1. Background gradient #1A1D2E to #16213E
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, QColor("#1A1D2E"))
        gradient.setColorAt(1.0, QColor("#16213E"))
        painter.fillRect(self.rect(), gradient)
        
        # 2. Draw company initial circle 'HT'
        center_x = self.width() / 2
        circle_y = 100
        circle_radius = 45
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#4F46E5"))
        painter.drawEllipse(int(center_x - circle_radius), int(circle_y - circle_radius), int(circle_radius * 2), int(circle_radius * 2))
        
        painter.setPen(QColor("#FFFFFF"))
        font = QFont("Segoe UI", 32, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(int(center_x - circle_radius), int(circle_y - circle_radius), int(circle_radius * 2), int(circle_radius * 2), Qt.AlignmentFlag.AlignCenter, "HT")
        
        # 3. Draw company name
        font = QFont("Segoe UI", 24, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(0, 180, self.width(), 40, Qt.AlignmentFlag.AlignCenter, "Hamza Travels & Tours")
        
        # 4. Draw subtitle
        painter.setPen(QColor("#4F46E5"))
        font = QFont("Segoe UI", 12)
        painter.setFont(font)
        painter.drawText(0, 220, self.width(), 30, Qt.AlignmentFlag.AlignCenter, "Travel Agency Management System")
        
        # 5. Draw version
        painter.setPen(QColor("#8892B0"))
        font = QFont("Segoe UI", 10)
        painter.setFont(font)
        painter.drawText(0, 250, self.width(), 20, Qt.AlignmentFlag.AlignCenter, "v1.0.0")
        
        # 6. Draw status text
        painter.setPen(QColor("#E2E8F0"))
        painter.drawText(20, self.height() - 25, self.width() - 40, 20, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom, self._status)
        
        # 7. Draw progress line
        progress_width = int(self.width() * self._progress)
        painter.fillRect(0, self.height() - 3, progress_width, 3, QColor("#4F46E5"))
        
        painter.end()
    
    def set_status(self, message: str):
        self._status = message
        self.showMessage(message, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft, QColor("#00000000")) # Transparent standard message since we custom paint
        self.repaint()
        
    def _animate_progress(self):
        self._progress += 0.01
        if self._progress > 1.0:
            self._progress = 0.0
        self.repaint()
