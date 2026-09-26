from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QTabWidget, QTableWidget, 
                               QHeaderView, QDateEdit, QTableWidgetItem, QMessageBox,
                               QFrame, QGridLayout, QComboBox, QAbstractItemView)
from PySide6.QtCore import QDate, Qt, QThread, Signal
from PySide6.QtGui import QColor
from services.report_service import ReportService
from ui.components.modern_widgets import GlowCard

class ReportWorker(QThread):
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, start_date, end_date):
        super().__init__()
        self.start_date = start_date
        self.end_date = end_date

    def run(self):
        try:
            service = ReportService()
            data = service.get_financial_statement_report(self.start_date, self.end_date)
            self.finished.emit(data)
        except Exception as e:
            self.error.emit(str(e))


class FinancialReportsPage(QWidget):
    def __init__(self, current_user, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.worker = None
        self._setup_ui()
        self.load_report()

    def showEvent(self, event):
        super().showEvent(event)
        # #region agent log
        try:
            import json, time
            open(r"E:\Customized Travel Agency System\debug-5da8ec.log", "a", encoding="utf-8").write(json.dumps({"sessionId":"5da8ec","hypothesisId":"D","location":"reports_page.py:showEvent","message":"reports page shown","data":{"has_current_data":hasattr(self,"current_data")},"timestamp":int(time.time()*1000)})+"\n")
        except Exception:
            pass
        # #endregion
        
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Header Area
        header = QHBoxLayout()
        title = QLabel("Financial Reports")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        # Date Filters
        filter_layout = QHBoxLayout()
        
        self.combo_date_range = QComboBox()
        self.combo_date_range.addItems(["This Month", "Today", "This Week", "This Year", "Custom"])
        self.combo_date_range.currentIndexChanged.connect(self._on_date_range_changed)
        
        self.date_from = QDateEdit(QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True)
        self.date_to = QDateEdit(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        
        btn_refresh = QPushButton("Refresh Report")
        btn_refresh.clicked.connect(self.load_report)
        btn_refresh.setObjectName("btn_primary")
        btn_refresh.setShortcut("Return")
        
        self.btn_export = QPushButton("Export PDF")
        self.btn_export.clicked.connect(self.export_pdf)
        self.btn_export.setObjectName("btn_success")
        self.btn_export.setEnabled(False) # Enable when report loads
        
        filter_layout.addWidget(QLabel("Date Range:"))
        filter_layout.addWidget(self.combo_date_range)
        filter_layout.addWidget(QLabel("From:"))
        filter_layout.addWidget(self.date_from)
        filter_layout.addWidget(QLabel("To:"))
        filter_layout.addWidget(self.date_to)
        filter_layout.addWidget(btn_refresh)
        filter_layout.addWidget(self.btn_export)
        
        header.addWidget(title)
        header.addStretch()
        header.addLayout(filter_layout)
        
        self._on_date_range_changed() # Apply initial preset
        
        main_layout.addLayout(header)
        
        # Content Layout (Sidebar + Tabs)
        content_layout = QHBoxLayout()
        
        # --- LEFT SIDEBAR (Summary) ---
        sidebar = GlowCard()
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar.setFixedWidth(300)
        
        lbl_summary_title = QLabel("Financial Summary")
        lbl_summary_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #E2E8F0;")
        sidebar_layout.addWidget(lbl_summary_title)
        
        # KPIs
        self.lbl_gross_rev = self._create_kpi_row(sidebar_layout, "Gross Revenue:")
        self.lbl_cogs = self._create_kpi_row(sidebar_layout, "Cost of Services (COGS):")
        
        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.HLine)
        line1.setStyleSheet("background-color: #334155;")
        sidebar_layout.addWidget(line1)
        
        self.lbl_gross_profit = self._create_kpi_row(sidebar_layout, "Gross Profit:")
        self.lbl_opex = self._create_kpi_row(sidebar_layout, "Operating Expenses:")
        
        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setStyleSheet("background-color: #334155;")
        sidebar_layout.addWidget(line2)
        
        self.lbl_net_profit = self._create_kpi_row(sidebar_layout, "Net Profit:")
        self.lbl_net_profit.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        sidebar_layout.addSpacing(20)
        
        self.lbl_cash_collections = self._create_kpi_row(sidebar_layout, "Cash Collected:")
        self.lbl_cash_collections.setStyleSheet("color: #10B981;")
        
        self.lbl_bank_collections = self._create_kpi_row(sidebar_layout, "Bank Collected:")
        self.lbl_bank_collections.setStyleSheet("color: #10B981;")
        
        self.lbl_cash_expenses = self._create_kpi_row(sidebar_layout, "Cash Expenses:")
        self.lbl_cash_expenses.setStyleSheet("color: #EF4444;")
        
        self.lbl_bank_expenses = self._create_kpi_row(sidebar_layout, "Bank Expenses:")
        self.lbl_bank_expenses.setStyleSheet("color: #EF4444;")
        
        self.lbl_vendor_cash = self._create_kpi_row(sidebar_layout, "Vendor Payments (Cash):")
        self.lbl_vendor_cash.setStyleSheet("color: #EF4444;")
        
        self.lbl_vendor_bank = self._create_kpi_row(sidebar_layout, "Vendor Payments (Bank):")
        self.lbl_vendor_bank.setStyleSheet("color: #EF4444;")
        
        line3 = QFrame()
        line3.setFrameShape(QFrame.Shape.HLine)
        line3.setStyleSheet("background-color: #334155;")
        sidebar_layout.addWidget(line3)
        
        self.lbl_net_cash = self._create_kpi_row(sidebar_layout, "Net Cash In Till:")
        self.lbl_net_cash.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        self.lbl_net_bank = self._create_kpi_row(sidebar_layout, "Net Bank Balance:")
        self.lbl_net_bank.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        sidebar_layout.addStretch()
        content_layout.addWidget(sidebar)
        
        # --- RIGHT PANEL (Tabs) ---
        self.tabs = QTabWidget()
        
        # Tab 1: P&L Statement (Itemized)
        self.tab_pnl = QWidget()
        l_pnl = QVBoxLayout(self.tab_pnl)
        self.tbl_pnl = QTableWidget(0, 2)
        self.tbl_pnl.setHorizontalHeaderLabels(["Account / Category", "Amount"])
        self.tbl_pnl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_pnl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        l_pnl.addWidget(self.tbl_pnl)
        self.lbl_pnl_footer = self._create_pnl_footer(l_pnl)
        self.tabs.addTab(self.tab_pnl, "📊 Profit & Loss Statement")
        
        # Tab 2: Cash Flow Log
        self.tab_cash = QWidget()
        l_cash = QVBoxLayout(self.tab_cash)
        self.tbl_cash = QTableWidget(0, 5)
        self.tbl_cash.setHorizontalHeaderLabels(["Date", "Ref #", "Party / Customer", "Type", "Amount"])
        self.tbl_cash.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_cash.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.tbl_cash.setColumnWidth(3, 80)
        self.tbl_cash.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        l_cash.addWidget(self.tbl_cash)
        self.lbl_cash_footer = self._create_flow_footer(l_cash)
        self.tabs.addTab(self.tab_cash, "💵 Cash Flow Log")
        
        # Tab 3: Bank Flow Log
        self.tab_bank = QWidget()
        l_bank = QVBoxLayout(self.tab_bank)
        self.tbl_bank = QTableWidget(0, 5)
        self.tbl_bank.setHorizontalHeaderLabels(["Date", "Ref #", "Party / Customer", "Type", "Amount"])
        self.tbl_bank.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_bank.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.tbl_bank.setColumnWidth(3, 80)
        self.tbl_bank.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        l_bank.addWidget(self.tbl_bank)
        self.lbl_bank_footer = self._create_flow_footer(l_bank)
        self.tabs.addTab(self.tab_bank, "🏦 Bank Flow Log")
        
        content_layout.addWidget(self.tabs)
        main_layout.addLayout(content_layout)
        
    def _create_pnl_footer(self, parent_layout):
        """Creates a bold footer bar showing final net profit / loss."""
        footer = QFrame()
        footer.setFixedHeight(48)
        footer.setStyleSheet("""
            QFrame { background-color: #1E293B; border-top: 2px solid #334155; border-radius: 0px; }
            QLabel { font-size: 15px; font-weight: bold; padding: 0 16px; }
        """)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(12, 0, 12, 0)
        lbl_title = QLabel("NET PROFIT / LOSS")
        lbl_title.setStyleSheet("color: #94A3B8; font-size: 15px; font-weight: bold;")
        self._lbl_pnl_value = QLabel("Rs. 0.00")
        self._lbl_pnl_value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._lbl_pnl_value.setStyleSheet("color: #F8FAFC; font-size: 18px; font-weight: bold;")
        footer_layout.addWidget(lbl_title)
        footer_layout.addStretch()
        footer_layout.addWidget(self._lbl_pnl_value)
        parent_layout.addWidget(footer)
        return self._lbl_pnl_value

    def _create_flow_footer(self, parent_layout):
        """Creates a styled footer bar under a flow table, returns the QLabel to update."""
        footer = QFrame()
        footer.setFixedHeight(40)
        footer.setStyleSheet("""
            QFrame { background-color: #1E293B; border-top: 1px solid #334155; border-radius: 0px; }
            QLabel { color: #E2E8F0; font-size: 13px; font-weight: bold; padding: 0 12px; }
        """)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(8, 0, 8, 0)
        lbl = QLabel("Transactions: 0   |   Total IN: Rs. 0.00   |   Total OUT: Rs. 0.00   |   Net: Rs. 0.00")
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        footer_layout.addWidget(lbl)
        parent_layout.addWidget(footer)
        return lbl

    def _create_kpi_row(self, layout, title):
        row = QHBoxLayout()
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: #94A3B8;")
        lbl_val = QLabel("Rs. 0.00")
        lbl_val.setAlignment(Qt.AlignmentFlag.AlignRight)
        lbl_val.setStyleSheet("font-weight: bold; color: #F8FAFC;")
        
        row.addWidget(lbl_title)
        row.addWidget(lbl_val)
        layout.addLayout(row)
        return lbl_val

    def _on_date_range_changed(self):
        selection = self.combo_date_range.currentText()
        today = QDate.currentDate()
        
        if selection == "Custom":
            self.date_from.setEnabled(True)
            self.date_to.setEnabled(True)
        else:
            self.date_from.setEnabled(False)
            self.date_to.setEnabled(False)
            
            if selection == "Today":
                self.date_from.setDate(today)
                self.date_to.setDate(today)
            elif selection == "This Week":
                day_of_week = today.dayOfWeek()
                start_of_week = today.addDays(-(day_of_week - 1))
                self.date_from.setDate(start_of_week)
                self.date_to.setDate(today)
            elif selection == "This Month":
                start_of_month = QDate(today.year(), today.month(), 1)
                self.date_from.setDate(start_of_month)
                self.date_to.setDate(today)
            elif selection == "This Year":
                start_of_year = QDate(today.year(), 1, 1)
                self.date_from.setDate(start_of_year)
                self.date_to.setDate(today)

    def load_report(self):
        if self.worker and self.worker.isRunning():
            return
            
        start_date = self.date_from.date().toPython()
        end_date = self.date_to.date().toPython()
        # #region agent log
        try:
            import json as _json
            with open(r"E:\Customized Travel Agency System\debug-5da8ec.log", "a", encoding="utf-8") as _f:
                _f.write(_json.dumps({"sessionId":"5da8ec","hypothesisId":"D","location":"reports_page.py:load_report","message":"load_report_called","data":{"start_date":str(start_date),"end_date":str(end_date),"preset":self.combo_date_range.currentText()},"timestamp":int(__import__("time").time()*1000)})+"\n")
        except Exception:
            pass
        # #endregion
        # #region agent log
        try:
            import json, time
            open(r"E:\Customized Travel Agency System\debug-5da8ec.log", "a", encoding="utf-8").write(json.dumps({"sessionId":"5da8ec","hypothesisId":"A","location":"reports_page.py:load_report","message":"report reload started","data":{"start_date":str(start_date),"end_date":str(end_date),"preset":self.combo_date_range.currentText()},"timestamp":int(time.time()*1000)})+"\n")
        except Exception:
            pass
        # #endregion
        
        self.worker = ReportWorker(start_date, end_date)
        self.worker.finished.connect(self._on_report_loaded)
        self.worker.error.connect(self._on_report_error)
        self.worker.start()

    def _on_report_loaded(self, data):
        self.current_data = data
        self.btn_export.setEnabled(True)
        
        # Update Sidebar
        self.lbl_gross_rev.setText(f"Rs. {data.get('gross_revenue', 0.0):,.2f}")
        self.lbl_cogs.setText(f"Rs. {data.get('cogs', 0.0):,.2f}")
        self.lbl_gross_profit.setText(f"Rs. {data.get('gross_profit', 0.0):,.2f}")
        self.lbl_opex.setText(f"Rs. {data.get('total_expenses', 0.0):,.2f}")
        
        net_profit = data.get('net_profit', 0.0)
        self.lbl_net_profit.setText(f"Rs. {net_profit:,.2f}")
        if net_profit >= 0:
            self.lbl_net_profit.setStyleSheet("font-size: 18px; font-weight: bold; color: #10B981;")
        else:
            self.lbl_net_profit.setStyleSheet("font-size: 18px; font-weight: bold; color: #EF4444;")
            
        collections_cash = data.get('collections_cash', 0.0)
        collections_bank = data.get('collections_bank', 0.0)
        self.lbl_cash_collections.setText(f"Rs. {collections_cash:,.2f}")
        self.lbl_bank_collections.setText(f"Rs. {collections_bank:,.2f}")
        
        expenses_cash = data.get('expenses_cash', 0.0)
        expenses_bank = data.get('expenses_bank', 0.0)
        self.lbl_cash_expenses.setText(f"Rs. {expenses_cash:,.2f}")
        self.lbl_bank_expenses.setText(f"Rs. {expenses_bank:,.2f}")
        
        vendor_cash = data.get('vendor_payments_cash', 0.0)
        vendor_bank = data.get('vendor_payments_bank', 0.0)
        self.lbl_vendor_cash.setText(f"Rs. {vendor_cash:,.2f}")
        self.lbl_vendor_bank.setText(f"Rs. {vendor_bank:,.2f}")
        
        net_cash = collections_cash - (expenses_cash + vendor_cash)
        net_bank = collections_bank - (expenses_bank + vendor_bank)
        
        self.lbl_net_cash.setText(f"Rs. {net_cash:,.2f}")
        if net_cash >= 0:
            self.lbl_net_cash.setStyleSheet("font-size: 16px; font-weight: bold; color: #10B981;")
        else:
            self.lbl_net_cash.setStyleSheet("font-size: 16px; font-weight: bold; color: #EF4444;")
            
        self.lbl_net_bank.setText(f"Rs. {net_bank:,.2f}")
        if net_bank >= 0:
            self.lbl_net_bank.setStyleSheet("font-size: 16px; font-weight: bold; color: #10B981;")
        else:
            self.lbl_net_bank.setStyleSheet("font-size: 16px; font-weight: bold; color: #EF4444;")
        
        # Update P&L Table (Itemized Expenses)
        expenses = data.get('itemized_expenses', [])
        self.tbl_pnl.setRowCount(0)
        
        # Add Sales and COGS as top line items for context
        self._add_pnl_row("Gross Sales", data.get('gross_revenue', 0.0))
        self._add_pnl_row("Cost of Services (COGS)", -data.get('cogs', 0.0))
        
        for exp in expenses:
            self._add_pnl_row(f"OpEx: {exp.get('account')}", -exp.get('amount', 0.0))
        
        # Update P&L footer with final net profit / loss
        net_profit = data.get('net_profit', 0.0)
        self.lbl_pnl_footer.setText(f"Rs. {net_profit:,.2f}")
        if net_profit >= 0:
            self.lbl_pnl_footer.setStyleSheet("color: #10B981; font-size: 18px; font-weight: bold;")
        else:
            self.lbl_pnl_footer.setStyleSheet("color: #EF4444; font-size: 18px; font-weight: bold;")
            
        # Update Cash Flow / Bank Flow Tables
        all_entries = data.get('receipts_log', [])  # fixed key: receipts_log not receipts_list
        
        # Split into Cash and Bank based on normalized payment_method ('Cash' or 'Bank')
        cash_entries = [r for r in all_entries if r.get("payment_method", "Cash") != "Bank"]
        bank_entries = [r for r in all_entries if r.get("payment_method", "") == "Bank"]
        # #region agent log
        try:
            import json as _json
            _trf_all = [r for r in all_entries if str(r.get("receipt_number","")).startswith("TRF-")]
            _trf_cash = [r for r in cash_entries if str(r.get("receipt_number","")).startswith("TRF-")]
            _trf_bank = [r for r in bank_entries if str(r.get("receipt_number","")).startswith("TRF-")]
            with open(r"E:\Customized Travel Agency System\debug-5da8ec.log", "a", encoding="utf-8") as _f:
                _f.write(_json.dumps({"sessionId":"5da8ec","hypothesisId":"C","location":"reports_page.py:_on_report_loaded","message":"flow_tables_split","data":{"all":len(all_entries),"cash":len(cash_entries),"bank":len(bank_entries),"trf_all":len(_trf_all),"trf_cash":len(_trf_cash),"trf_bank":len(_trf_bank),"sample_methods":list({str(r.get("payment_method")) for r in all_entries})},"timestamp":int(__import__("time").time()*1000)})+"\n")
        except Exception:
            pass
        # #endregion
        
        def _fill_flow_table(table, footer_lbl, entries):
            table.setRowCount(0)
            total_in = 0.0
            total_out = 0.0
            for row_idx, r in enumerate(entries):
                table.insertRow(row_idx)
                table.setItem(row_idx, 0, QTableWidgetItem(r.get("date", "")))
                table.setItem(row_idx, 1, QTableWidgetItem(r.get("receipt_number", "")))
                # Show the party/customer label — already enriched with category | description | bank
                table.setItem(row_idx, 2, QTableWidgetItem(r.get("customer", "")))
                r_type = r.get("type", "IN")
                type_item = QTableWidgetItem("IN" if r_type == "IN" else "OUT")
                type_item.setTextAlignment(int(Qt.AlignmentFlag.AlignCenter))
                if r_type == "OUT":
                    type_item.setForeground(QColor("#EF4444"))
                    total_out += r.get("amount", 0.0)
                else:
                    type_item.setForeground(QColor("#10B981"))
                    total_in += r.get("amount", 0.0)
                table.setItem(row_idx, 3, type_item)
                amt_item = QTableWidgetItem(f"Rs. {r.get('amount', 0.0):,.2f}")
                amt_item.setTextAlignment(int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter))
                if r_type == "OUT":
                    amt_item.setForeground(QColor("#EF4444"))
                else:
                    amt_item.setForeground(QColor("#10B981"))
                table.setItem(row_idx, 4, amt_item)
            
            # Update footer
            net = total_in - total_out
            net_color = "#10B981" if net >= 0 else "#EF4444"
            footer_lbl.setText(
                f"Transactions: {len(entries)}   |   "
                f"Total IN: <span style='color:#10B981'>Rs. {total_in:,.2f}</span>   |   "
                f"Total OUT: <span style='color:#EF4444'>Rs. {total_out:,.2f}</span>   |   "
                f"Net: <span style='color:{net_color}'>Rs. {net:,.2f}</span>"
            )
        
        _fill_flow_table(self.tbl_cash, self.lbl_cash_footer, cash_entries)
        _fill_flow_table(self.tbl_bank, self.lbl_bank_footer, bank_entries)

    def _add_pnl_row(self, title, amount):
        row = self.tbl_pnl.rowCount()
        self.tbl_pnl.insertRow(row)
        self.tbl_pnl.setItem(row, 0, QTableWidgetItem(title))
        
        amt_item = QTableWidgetItem(f"Rs. {amount:,.2f}")
        amt_item.setTextAlignment(int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter))
        if amount < 0:
            amt_item.setForeground(Qt.GlobalColor.red)
        self.tbl_pnl.setItem(row, 1, amt_item)

    def _on_report_error(self, err_msg):
        QMessageBox.warning(self, "Report Error", f"Failed to load financial report:\n{err_msg}")

    def export_pdf(self):
        if not hasattr(self, 'current_data') or not self.current_data:
            return
            
        import os
        from services.pdf_service import PDFService
        start_date = self.date_from.date().toPython()
        end_date = self.date_to.date().toPython()
        
        try:
            pdf_service = PDFService()
            filepath = pdf_service.generate_financial_report(self.current_data, start_date, end_date)
            os.startfile(filepath)
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export PDF:\n{str(e)}")
