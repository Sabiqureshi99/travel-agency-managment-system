import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor

def get_resource_path(relative_path):
    """Safely find files whether running as a .py script or a compiled .exe"""
    if hasattr(sys, '_MEIPASS'):
        # Running as a compiled .exe
        base_path = sys._MEIPASS
    else:
        # Running from Python source code
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class Colors:
    # Dark theme
    DARK_BG = '#0F1117'
    DARK_CARD = '#1A1D2E'
    DARK_SIDEBAR = '#1A1D2E'
    DARK_BORDER = '#2A2D3E'
    DARK_INPUT = '#252836'
    DARK_TEXT = '#E2E8F0'
    DARK_TEXT_SECONDARY = '#8892B0'
    # Light theme
    LIGHT_BG = '#F0F2F5'
    LIGHT_CARD = '#FFFFFF'
    LIGHT_BORDER = '#E2E8F0'
    LIGHT_TEXT = '#1E293B'
    # Shared
    ACCENT = '#4F46E5'
    ACCENT_HOVER = '#4338CA'
    DANGER = '#DC2626'
    SUCCESS = '#16A34A'
    WARNING = '#D97706'
    INFO = '#0EA5E9'

class ThemeManager:
    _current_theme: str = 'dark'
    _app: QApplication | None = None
    _STYLES_DIR = Path(__file__).parent
    
    @classmethod
    def apply(cls, app: QApplication, theme: str | None = None) -> None:
        cls._app = app
        if theme:
            cls._current_theme = theme
            
        # Use get_resource_path to find the stylesheet
        relative_path = os.path.join("ui", "styles", f"{cls._current_theme}_theme.qss")
        style_file = get_resource_path(relative_path)
        
        try:
            with open(style_file, 'r', encoding='utf-8') as f:
                app.setStyleSheet(f.read())
        except FileNotFoundError:
            print(f"Warning: Stylesheet {style_file} not found.")
    
    @classmethod
    def toggle(cls) -> str:
        cls._current_theme = 'light' if cls._current_theme == 'dark' else 'dark'
        if cls._app:
            cls.apply(cls._app)
        return cls._current_theme
    
    @classmethod
    def current_theme(cls) -> str:
        return cls._current_theme
    
    @classmethod
    def is_dark(cls) -> bool:
        return cls._current_theme == 'dark'
    
    @classmethod
    def get_icon_color(cls) -> str:
        return Colors.DARK_TEXT if cls.is_dark() else Colors.LIGHT_TEXT
    
    @classmethod
    def get_accent_color(cls) -> str:
        return Colors.ACCENT
    
    @classmethod
    def get_card_color(cls) -> str:
        return Colors.DARK_CARD if cls.is_dark() else Colors.LIGHT_CARD
    
    @classmethod
    def get_bg_color(cls) -> str:
        return Colors.DARK_BG if cls.is_dark() else Colors.LIGHT_BG
