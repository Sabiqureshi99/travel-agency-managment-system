from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLineEdit, QListView, 
                             QApplication, QFrame)
from PySide6.QtCore import Qt, Signal, QSortFilterProxyModel, QAbstractListModel, QModelIndex

class SearchListModel(QAbstractListModel):
    def __init__(self, data=None, parent=None):
        super().__init__(parent)
        self._data = data or [] # list of dicts: {'id': '123', 'text': 'John Doe'}
        
    def rowCount(self, parent=QModelIndex()):
        return len(self._data)
        
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        row = index.row()
        if role == Qt.ItemDataRole.DisplayRole:
            return self._data[row].get('text')
        elif role == Qt.ItemDataRole.UserRole:
            return self._data[row].get('id')
        return None

class SearchableComboBox(QFrame):
    item_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        
        self.popup_list = QListView(self)
        self.popup_list.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        self.popup_list.setMouseTracking(True)
        # Force style inheritance if needed
        self.popup_list.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.popup_list.setStyleSheet("""
            QListView {
                background-color: #1E1E2E;
                color: #FFFFFF;
                border: 1px solid #FF3366;
                border-radius: 4px;
                outline: 0;
            }
            QListView::item {
                padding: 8px;
            }
            QListView::item:hover, QListView::item:selected {
                background-color: #FF3366;
                color: white;
            }
        """)
        
        self.source_model = SearchListModel()
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.source_model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        
        self.popup_list.setModel(self.proxy_model)
        
        layout.addWidget(self.search_input)
        
        # Connect signals
        self.search_input.textChanged.connect(self.proxy_model.setFilterFixedString)
        self.search_input.textChanged.connect(self.show_popup)
        self.search_input.textEdited.connect(self.show_popup)
        self.popup_list.clicked.connect(self._on_item_clicked)
        
    def set_data(self, data_list):
        """data_list should be a list of tuples: (display_text, hidden_id)"""
        formatted = [{'text': t, 'id': i} for t, i in data_list]
        self.source_model = SearchListModel(formatted)
        self.proxy_model.setSourceModel(self.source_model)
        
    def show_popup(self):
        if self.proxy_model.rowCount() > 0 and self.search_input.text():
            pos = self.mapToGlobal(self.rect().bottomLeft())
            self.popup_list.move(pos)
            self.popup_list.setFixedWidth(self.width())
            # Calculate height
            row_height = 32
            max_rows = 5
            rows = min(self.proxy_model.rowCount(), max_rows)
            self.popup_list.setFixedHeight(rows * row_height + 2)
            self.popup_list.show()
        else:
            self.popup_list.hide()
            
    def _on_item_clicked(self, index):
        if index.isValid():
            item_id = self.proxy_model.data(index, Qt.ItemDataRole.UserRole)
            item_text = self.proxy_model.data(index, Qt.ItemDataRole.DisplayRole)
            
            self.search_input.blockSignals(True)
            self.search_input.setText(item_text)
            self.search_input.blockSignals(False)
            
            self.popup_list.hide()
            self.item_selected.emit(item_id)
