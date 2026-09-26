from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QSpacerItem, QSizePolicy
from PySide6.QtCore import Signal, Qt

class PaginationWidget(QWidget):
    page_changed = Signal(int)

    def __init__(self, total_pages=1, current_page=1, parent=None):
        super().__init__(parent)
        self.total_pages = max(1, total_pages)
        self.current_page = current_page

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.prev_btn = QPushButton("Previous")
        self.prev_btn.clicked.connect(self.go_previous)
        
        self.next_btn = QPushButton("Next")
        self.next_btn.clicked.connect(self.go_next)

        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout.addWidget(self.prev_btn)
        self.layout.addWidget(self.info_label, 1)
        self.layout.addWidget(self.next_btn)

        self.update_ui()

    def update_ui(self):
        self.info_label.setText(f"Page {self.current_page} of {self.total_pages}")
        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page < self.total_pages)

    def set_total_pages(self, total):
        self.total_pages = max(1, total)
        if self.current_page > self.total_pages:
            self.current_page = max(1, self.total_pages)
        self.update_ui()

    def set_current_page(self, page):
        if 1 <= page <= self.total_pages:
            self.current_page = page
            self.update_ui()
            self.page_changed.emit(self.current_page)

    def go_previous(self):
        self.set_current_page(self.current_page - 1)

    def go_next(self):
        self.set_current_page(self.current_page + 1)
