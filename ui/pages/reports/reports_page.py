from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QTableWidget, QHeaderView, 
                               QFormLayout, QDateEdit, QMessageBox, QFileDialog, QAbstractItemView, QTableWidgetItem, QAbstractItemView)
from PySide6.QtCore import QDate, Qt
from viewmodels.reports_viewmodel import ReportsViewModel
from utils.formatters import format_currency, format_date

class ReportsPage(QWidget):
    def __init__(self, current_user, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.viewmodel = ReportsViewModel()
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        
        header = QHBoxLayout()
        title = QLabel("Financial Reports")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #FFFFFF;")
        
        self.btn_export = QPushButton("📤 Export to CSV")
        self.btn_export.setObjectName("btn_success")
        self.btn_export.setFixedWidth(140)
        self.btn_export.setEnabled(False)
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.btn_export)
        layout.addLayout(header)
        
        main_area = QHBoxLayout()
        
        # Left Panel (Params & Summary)
        left_panel_widget = QWidget()
        left_panel_widget.setFixedWidth(300)
        left_panel = QVBoxLayout(left_panel_widget)
        left_panel.setContentsMargins(0, 0, 0, 0)
        
        params_frame = QFrame()
        params_frame.setStyleSheet("""
            QFrame {
                background: #252836;
                border-radius: 8px;
                padding: 10px;
            }
            QLabel { color: #E2E8F0; }
        """)
        params_layout = QFormLayout(params_frame)
        self.date_from = QDateEdit(QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True)
        self.date_to = QDateEdit(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        
        self.btn_generate = QPushButton("Generate Report")
        self.btn_generate.setObjectName("btn_primary")
        self.btn_generate.setShortcut("Return")
        
        params_layout.addRow("From Date:", self.date_from)
        params_layout.addRow("To Date:", self.date_to)
        params_layout.addRow("", self.btn_generate)
        left_panel.addWidget(params_frame)
        
        # Summary Frame
        self.summary_frame = QFrame()
        self.summary_frame.setStyleSheet("""
            QFrame {
                background: #252836;
                border-radius: 8px;
                padding: 15px;
            }
            QLabel { color: #E2E8F0; }
        """)
        summary_layout = QVBoxLayout(self.summary_frame)
        self.lbl_revenue = QLabel("Total Income: Rs. 0.00")
        self.lbl_expenses = QLabel("Total Expenses: Rs. 0.00")
        self.lbl_profit = QLabel("Net Profit: Rs. 0.00")
        
        for lbl in (self.lbl_revenue, self.lbl_expenses, self.lbl_profit):
            lbl.setStyleSheet("font-size: 14px; font-weight: bold;")
            summary_layout.addWidget(lbl)
            
        left_panel.addWidget(self.summary_frame)
        left_panel.addStretch()
        
        main_area.addWidget(left_panel_widget)
        
        # Right Panel (Table)
        self.tbl_report = QTableWidget(0, 5)
        self.tbl_report.setHorizontalHeaderLabels(["Date", "Type", "Reference", "Description", "Amount"])
        self.tbl_report.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_report.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_report.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl_report.verticalHeader().setVisible(False)
        self.tbl_report.setStyleSheet("""
            QTableWidget {
                background-color: #252836;
                border: 1px solid #2A2D3E;
                border-radius: 8px;
                color: #E2E8F0;
            }
            QHeaderView::section {
                background-color: transparent;
                color: #8892B0;
                font-weight: bold;
                border: none;
                border-bottom: 1px solid #2A2D3E;
                padding: 8px;
            }
        """)
        main_area.addWidget(self.tbl_report)
        
        layout.addLayout(main_area)

    def _connect_signals(self):
        self.btn_generate.clicked.connect(self._generate_report)
        self.btn_export.clicked.connect(self._export_csv)
        self.viewmodel.report_generated.connect(self._on_report_generated)
        self.viewmodel.export_completed.connect(lambda p: QMessageBox.information(self, "Export Successful", f"Report exported to {p}"))
        self.viewmodel.export_failed.connect(lambda e: QMessageBox.critical(self, "Export Failed", e))
        
    def _generate_report(self):
        start_date = self.date_from.date().toPython()
        end_date = self.date_to.date().toPython()
        self.btn_generate.setEnabled(False)
        self.btn_generate.setText("Generating...")
        self.viewmodel.generate_report(start_date, end_date)
        
    def _on_report_generated(self, data):
        self.btn_generate.setEnabled(True)
        self.btn_generate.setText("Generate Report")
        self.btn_export.setEnabled(True)
        
        # Update summary
        self.lbl_revenue.setText(f"Total Income: {format_currency(data['total_revenue'])}")
        self.lbl_expenses.setText(f"Total Expenses: {format_currency(data['total_expenses'])}")
        self.lbl_profit.setText(f"Net Profit: {format_currency(data['net_profit'])}")
        
        # Determine profit color
        if data['net_profit'] >= 0:
            self.lbl_profit.setStyleSheet("font-size: 16px; font-weight: bold; color: #10B981;") # Green
        else:
            self.lbl_profit.setStyleSheet("font-size: 16px; font-weight: bold; color: #EF4444;") # Red
        
        # Populate table
        items = data.get('items', [])
        self.tbl_report.setRowCount(0)
        for row, item in enumerate(items):
            self.tbl_report.insertRow(row)
            self.tbl_report.setItem(row, 0, QTableWidgetItem(item['date']))
            
            type_item = QTableWidgetItem(item['type'])
            if item['type'] == 'Income':
                type_item.setForeground(Qt.GlobalColor.green)
            else:
                type_item.setForeground(Qt.GlobalColor.red)
                
            self.tbl_report.setItem(row, 1, type_item)
            self.tbl_report.setItem(row, 2, QTableWidgetItem(item['reference']))
            self.tbl_report.setItem(row, 3, QTableWidgetItem(item['description']))
            
            amt_item = QTableWidgetItem(format_currency(item['amount']))
            amt_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.tbl_report.setItem(row, 4, amt_item)

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Report", "Financial_Report.csv", "CSV Files (*.csv)")
        if path:
            self.viewmodel.export_to_csv(path)
