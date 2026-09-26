from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QHBoxLayout, QFrame
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QIcon

class PhotoUploadWidget(QWidget):
    photoSelected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_photo_path = None

        self.layout = QVBoxLayout(self)
        
        self.preview_label = QLabel("No Image Selected")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setFrameShape(QFrame.Shape.Box)
        self.preview_label.setFixedSize(200, 200)
        self.preview_label.setStyleSheet("background-color: #f0f0f0; color: #888; border: 2px dashed #ccc;")
        
        self.layout.addWidget(self.preview_label, alignment=Qt.AlignmentFlag.AlignCenter)

        btn_layout = QHBoxLayout()
        self.select_btn = QPushButton("Select Photo")
        self.select_btn.clicked.connect(self.select_photo)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_photo)
        self.clear_btn.setEnabled(False)

        btn_layout.addWidget(self.select_btn)
        btn_layout.addWidget(self.clear_btn)
        
        self.layout.addLayout(btn_layout)

    def select_photo(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Photo", "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.set_photo(file_path)

    def set_photo(self, file_path):
        self.current_photo_path = file_path
        pixmap = QPixmap(file_path)
        if not pixmap.isNull():
            # Scale pixmap keeping aspect ratio
            scaled_pixmap = pixmap.scaled(
                self.preview_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.preview_label.setPixmap(scaled_pixmap)
            self.clear_btn.setEnabled(True)
            self.photoSelected.emit(file_path)

    def clear_photo(self):
        self.current_photo_path = None
        self.preview_label.clear()
        self.preview_label.setText("No Image Selected")
        self.clear_btn.setEnabled(False)
        self.photoSelected.emit("")

    def get_photo_path(self):
        return self.current_photo_path
