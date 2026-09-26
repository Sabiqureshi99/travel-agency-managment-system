from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QPen

class LoadingOverlay(QWidget):
    def __init__(self, parent=None, message="Loading..."):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.label = QLabel(message)
        self.label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        self.layout.addWidget(self.label)
        
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        
        self.setVisible(False)

    def start(self, message=None):
        if message:
            self.label.setText(message)
        if self.parent():
            self.resize(self.parent().size())
        self.setVisible(True)
        self.raise_()
        self.timer.start(50)

    def stop(self):
        self.timer.stop()
        self.setVisible(False)

    def rotate(self):
        self.angle = (self.angle + 30) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw semi-transparent background
        painter.fillRect(self.rect(), QColor(0, 0, 0, 150))
        
        # Draw spinner
        center = self.rect().center()
        painter.translate(center.x(), center.y() - 40)
        painter.rotate(self.angle)
        
        pen = QPen(QColor(255, 255, 255))
        pen.setWidth(4)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        for i in range(12):
            painter.drawLine(15, 0, 25, 0)
            painter.rotate(30)
