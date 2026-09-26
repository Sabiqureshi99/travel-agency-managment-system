from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, Signal
import math

class PaginationWidget(QWidget):
    page_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.total = 0
        self.current_skip = 0
        self.limit = 50
        
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        
        layout.addStretch()
        
        self.btn_prev = QPushButton("◄ Previous")
        self.btn_prev.setObjectName("btn_secondary")
        self.btn_prev.setMinimumWidth(100)
        self.btn_prev.clicked.connect(self._on_prev)
        
        self.lbl_info = QLabel("Page 1 of 1 (0 Items)")
        self.lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_info.setMinimumWidth(200)
        
        self.btn_next = QPushButton("Next ►")
        self.btn_next.setObjectName("btn_secondary")
        self.btn_next.setMinimumWidth(100)
        self.btn_next.clicked.connect(self._on_next)
        
        layout.addWidget(self.btn_prev)
        layout.addWidget(self.lbl_info)
        layout.addWidget(self.btn_next)
        layout.addStretch()
        
        self._update_buttons()

    def update_pagination(self, total: int, current_skip: int, limit: int):
        self.total = total
        self.current_skip = current_skip
        self.limit = limit
        
        current_page = (self.current_skip // self.limit) + 1 if self.limit > 0 else 1
        total_pages = math.ceil(self.total / self.limit) if self.limit > 0 else 1
        total_pages = max(1, total_pages)
        
        self.lbl_info.setText(f"Page {current_page} of {total_pages} ({self.total} Items)")
        self._update_buttons()

    def _update_buttons(self):
        self.btn_prev.setEnabled(self.current_skip > 0)
        
        has_next = (self.current_skip + self.limit) < self.total
        self.btn_next.setEnabled(has_next)

    def _on_prev(self):
        if self.current_skip > 0:
            new_skip = max(0, self.current_skip - self.limit)
            self.page_changed.emit(new_skip)

    def _on_next(self):
        if (self.current_skip + self.limit) < self.total:
            new_skip = self.current_skip + self.limit
            self.page_changed.emit(new_skip)
