from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QComboBox, QDateEdit, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QDate, QRegularExpression
from PySide6.QtGui import QRegularExpressionValidator, QPalette, QColor, QValidator

class ValidatedLineEdit(QWidget):
    textChanged = Signal(str)

    def __init__(self, label_text="", regex_pattern=None, error_message="Invalid input", parent=None):
        super().__init__(parent)
        self.error_message = error_message
        self.is_valid = True

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(2)

        if label_text:
            self.label = QLabel(label_text)
            self.layout.addWidget(self.label)

        self.line_edit = QLineEdit()
        self.layout.addWidget(self.line_edit)

        self.error_label = QLabel(self.error_message)
        self.error_label.setStyleSheet("color: red; font-size: 10px;")
        self.error_label.setVisible(False)
        self.layout.addWidget(self.error_label)

        if regex_pattern:
            regex = QRegularExpression(regex_pattern)
            validator = QRegularExpressionValidator(regex)
            self.line_edit.setValidator(validator)

        self.line_edit.textChanged.connect(self._on_text_changed)
        self.line_edit.editingFinished.connect(self.validate)

    def _on_text_changed(self, text):
        self.error_label.setVisible(False)
        self.line_edit.setStyleSheet("")
        self.textChanged.emit(text)

    def validate(self):
        if self.line_edit.validator():
            state, _, _ = self.line_edit.validator().validate(self.line_edit.text(), 0)
            self.is_valid = (state == QValidator.State.Acceptable)
            if not self.is_valid and self.line_edit.text():
                self.error_label.setVisible(True)
                self.line_edit.setStyleSheet("border: 1px solid red;")
            else:
                self.error_label.setVisible(False)
                self.line_edit.setStyleSheet("")
        return self.is_valid

    def text(self):
        return self.line_edit.text()

    def setText(self, text):
        self.line_edit.setText(text)


class SearchableComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.completer().setCompletionMode(self.completer().CompletionMode.PopupCompletion)
        self.completer().setFilterMode(Qt.MatchFlag.MatchContains)


class DateRangeWidget(QWidget):
    rangeChanged = Signal(QDate, QDate)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate())

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate().addDays(7))

        layout.addWidget(QLabel("Start:"))
        layout.addWidget(self.start_date)
        layout.addWidget(QLabel("End:"))
        layout.addWidget(self.end_date)

        self.start_date.dateChanged.connect(self._check_range)
        self.end_date.dateChanged.connect(self._check_range)

    def _check_range(self):
        if self.start_date.date() > self.end_date.date():
            self.end_date.setDate(self.start_date.date())
        self.rangeChanged.emit(self.start_date.date(), self.end_date.date())

    def get_start_date(self):
        return self.start_date.date()

    def get_end_date(self):
        return self.end_date.date()
