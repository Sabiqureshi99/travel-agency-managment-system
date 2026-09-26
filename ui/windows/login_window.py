from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QCheckBox, QFrame, QGraphicsDropShadowEffect, QMessageBox)
from PySide6.QtCore import Qt, Signal, QPoint, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QLinearGradient, QColor, QFont, QCursor, QPainterPath

class LoginWindow(QWidget):
    login_successful = Signal(object)  # emits User
    
    def __init__(self):
        super().__init__()
        self._drag_pos = None
        self._failed_attempts = 0
        self._setup_ui()
        self._center_on_screen()
    
    def _setup_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setFixedSize(900, 550)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Container to hold everything and apply drop shadow if needed
        container = QFrame()
        container.setStyleSheet("QFrame { background-color: #0F1117; border-radius: 12px; }")
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # Left Panel (Gradient handled in paintEvent, so we use a transparent widget)
        self.left_panel = QWidget()
        self.left_panel.setFixedWidth(400)
        
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        logo_label = QLabel("HT")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet("color: white; font-size: 48px; font-weight: bold; background-color: #4F46E5; border-radius: 50px; min-width: 100px; max-width: 100px; min-height: 100px; max-height: 100px;")
        
        title_label = QLabel("Hamza Travels & Tours")
        title_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold; margin-top: 20px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        tagline_label = QLabel("Travel Agency Management System")
        tagline_label.setStyleSheet("color: #8892B0; font-size: 14px;")
        tagline_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet("color: #8892B0; font-size: 12px; margin-top: 50px;")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        left_layout.addWidget(logo_label, 0, Qt.AlignmentFlag.AlignHCenter)
        left_layout.addWidget(title_label)
        left_layout.addWidget(tagline_label)
        left_layout.addWidget(version_label)
        
        # Right Panel (Form area)
        right_panel = QFrame()
        right_panel.setStyleSheet("QFrame { background-color: #1A1D2E; border-top-right-radius: 12px; border-bottom-right-radius: 12px; }")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(50, 40, 50, 40)
        
        # Close button
        close_btn_layout = QHBoxLayout()
        close_btn_layout.addStretch()
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setStyleSheet("QPushButton { color: #8892B0; background: transparent; border: none; font-size: 16px; } QPushButton:hover { color: white; background: #DC2626; border-radius: 15px; }")
        self.close_btn.clicked.connect(self.close)
        close_btn_layout.addWidget(self.close_btn)
        right_layout.addLayout(close_btn_layout)
        
        right_layout.addStretch()
        
        welcome_label = QLabel("Welcome Back")
        welcome_label.setStyleSheet("color: white; font-size: 28px; font-weight: bold;")
        right_layout.addWidget(welcome_label)
        
        instruction_label = QLabel("Please sign in to your account")
        instruction_label.setStyleSheet("color: #8892B0; font-size: 14px; margin-bottom: 20px;")
        right_layout.addWidget(instruction_label)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setFixedHeight(45)
        self.username_input.setStyleSheet("QLineEdit { background: #252836; border: 1.5px solid #3D4060; border-radius: 6px; color: white; padding-left: 15px; font-size: 14px; } QLineEdit:focus { border-color: #4F46E5; }")
        right_layout.addWidget(self.username_input)
        
        right_layout.addSpacing(15)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFixedHeight(45)
        self.password_input.setStyleSheet("QLineEdit { background: #252836; border: 1.5px solid #3D4060; border-radius: 6px; color: white; padding-left: 15px; font-size: 14px; } QLineEdit:focus { border-color: #4F46E5; }")
        right_layout.addWidget(self.password_input)
        
        options_layout = QHBoxLayout()
        self.remember_me = QCheckBox("Remember me")
        self.remember_me.setStyleSheet("QCheckBox { color: #8892B0; font-size: 13px; } QCheckBox::indicator { width: 16px; height: 16px; border-radius: 4px; border: 1.5px solid #3D4060; background: #252836; } QCheckBox::indicator:checked { background: #4F46E5; border-color: #4F46E5; }")
        options_layout.addWidget(self.remember_me)
        
        self.forgot_btn = QPushButton("Forgot Password?")
        self.forgot_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.forgot_btn.setStyleSheet("QPushButton { color: #4F46E5; background: transparent; border: none; font-size: 13px; } QPushButton:hover { text-decoration: underline; }")
        options_layout.addWidget(self.forgot_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        right_layout.addLayout(options_layout)
        right_layout.addSpacing(20)
        
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: #DC2626; font-size: 13px;")
        self.error_label.hide()
        right_layout.addWidget(self.error_label)
        
        self.login_btn = QPushButton("Sign In")
        self.login_btn.setFixedHeight(45)
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.setStyleSheet("QPushButton { background: #4F46E5; color: white; border: none; border-radius: 6px; font-size: 15px; font-weight: bold; } QPushButton:hover { background: #4338CA; } QPushButton:pressed { background: #3730A3; }")
        self.login_btn.clicked.connect(self._attempt_login)
        right_layout.addWidget(self.login_btn)
        
        right_layout.addStretch()
        
        container_layout.addWidget(self.left_panel)
        container_layout.addWidget(right_panel)
        
        main_layout.addWidget(container)
        
    def paintEvent(self, event):
        super().paintEvent(event)
        # Custom paint for the left panel gradient
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Define rect for left panel
        rect = self.left_panel.geometry()
        
        path = QPainterPath()
        path.addRoundedRect(rect.x(), rect.y(), rect.width(), rect.height(), 12, 12)
        # We need to make sure the right side of the left panel is square so it meets the right panel
        path.addRect(rect.x() + rect.width() - 12, rect.y(), 12, rect.height())
        
        painter.setClipPath(path)
        
        gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        gradient.setColorAt(0.0, QColor("#1A1D2E"))
        gradient.setColorAt(1.0, QColor("#16213E"))
        
        painter.fillRect(rect, gradient)
        
    def _center_on_screen(self):
        screen = self.screen().geometry()
        size = self.geometry()
        self.move(int((screen.width() - size.width()) / 2),
                  int((screen.height() - size.height()) / 2))
    
    def _attempt_login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        if self._failed_attempts >= 5:
            self.error_label.setText("Account locked. Too many failed attempts.")
            self.error_label.show()
            return
            
        if not username or not password:
            self.error_label.setText("Please enter both username and password.")
            self.error_label.show()
            return
            
        from services.auth_service import auth_service
        from core.exceptions import AuthenticationError, AccountLockedError
        
        try:
            user = auth_service.login(username, password)
            self.error_label.hide()
            self.login_successful.emit(user)
        except AccountLockedError as e:
            self.error_label.setText(str(e))
            self.error_label.show()
        except AuthenticationError:
            self.error_label.setText("Invalid username or password.")
            self.error_label.show()
        except Exception as e:
            self.error_label.setText("An unexpected error occurred.")
            self.error_label.show()
            print(f"Login error: {e}")
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
    
    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
    
    def mouseReleaseEvent(self, event):
        self._drag_pos = None
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self._attempt_login()
        else:
            super().keyPressEvent(event)
