import cv2
import numpy as np
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, 
                               QPushButton, QHBoxLayout, QMessageBox)
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QImage, QPixmap

from services.ocr_service import OcrService, OcrServiceError

class CameraThread(QThread):
    change_pixmap_signal = Signal(np.ndarray)
    error_signal = Signal(str)

    def __init__(self):
        super().__init__()
        self._run_flag = True

    def run(self):
        # Open default camera with DirectShow backend for Windows
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        
        # Check if camera opened successfully
        if not cap.isOpened():
            self.error_signal.emit("Error: Could not open webcam.")
            return

        while self._run_flag:
            ret, cv_img = cap.read()
            if ret:
                self.change_pixmap_signal.emit(cv_img.copy())
            else:
                self.error_signal.emit("Error: Could not read frame from webcam.")
                break
                
        # Release the camera when the thread is stopped
        cap.release()

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.wait()


class ScannerDialog(QDialog):
    scan_successful = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Offline Passport MRZ Scanner")
        self.setFixedSize(800, 600)
        
        self.ocr_service = OcrService()
        
        # Check Tesseract installation immediately
        if not self.ocr_service.check_tesseract_installed():
            QMessageBox.critical(self, "Tesseract Missing", 
                                 "Tesseract-OCR is not installed or not in PATH.\n"
                                 "Please install Tesseract for Windows to use the Passport Scanner.")
            # We don't abort instantiation, but it won't work when they click capture.

        self._setup_ui()
        self._start_camera()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Info Label
        info = QLabel("Align the bottom of the passport (the Machine Readable Zone) in the camera view.")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("color: #8B8B9E; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(info)
        
        # Video Feed Label
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background-color: #12121E; border: 2px solid #2A2A40; border-radius: 12px;")
        self.image_label.setMinimumSize(640, 480)
        layout.addWidget(self.image_label, stretch=1)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_capture = QPushButton("Capture & Read Passport")
        self.btn_capture.setFixedHeight(45)
        self.btn_capture.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #2563eb; }
        """)
        self.btn_capture.clicked.connect(self._on_capture_clicked)
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setFixedHeight(45)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #2A2A40;
                color: white;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #3F3F5A; }
        """)
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(self.btn_capture)
        layout.addLayout(btn_layout)
        
        # Store latest frame
        self._current_frame = None

    def _start_camera(self):
        self.thread = CameraThread()
        self.thread.change_pixmap_signal.connect(self._update_image)
        self.thread.error_signal.connect(self._on_camera_error)
        self.thread.start()

    @Slot(np.ndarray)
    def _update_image(self, cv_img):
        """Updates the image_label with a new opencv image"""
        self._current_frame = cv_img.copy() # Store a copy for OCR
        
        # Convert from OpenCV BGR format to Qt RGB format
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
        
        # Scale preserving aspect ratio
        p = convert_to_Qt_format.scaled(self.image_label.width(), self.image_label.height(), Qt.KeepAspectRatio)
        self.image_label.setPixmap(QPixmap.fromImage(p))
        
    @Slot(str)
    def _on_camera_error(self, err_msg):
        QMessageBox.warning(self, "Camera Error", err_msg)
        self.image_label.setText("Camera not found or unavailable.")

    def _on_capture_clicked(self):
        if self._current_frame is None:
            QMessageBox.warning(self, "Warning", "No camera frame available to scan.")
            return
            
        self.btn_capture.setText("Processing OCR...")
        self.btn_capture.setEnabled(False)
        
        # In a production app, we would run OCR in another thread to avoid 
        # freezing the UI for ~2 seconds. For simplicity, we run it synchronously here.
        try:
            data = self.ocr_service.extract_mrz_data(self._current_frame)
            self.scan_successful.emit(data)
            self.accept()
        except OcrServiceError as e:
            QMessageBox.warning(self, "Scan Failed", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unexpected error during OCR: {str(e)}")
        finally:
            self.btn_capture.setText("Capture & Read Passport")
            self.btn_capture.setEnabled(True)

    def closeEvent(self, event):
        """Ensure thread is properly stopped when dialog is closed"""
        if hasattr(self, 'thread') and self.thread.isRunning():
            self.thread.stop()
        super().closeEvent(event)
