import numpy as np
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                               QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
                               QAbstractItemView)
from PySide6.QtCore import Qt

import os
os.environ['QT_API'] = 'pyside6'

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from utils.formatters import format_currency, format_datetime
from ui.components.modern_widgets import KPIDashboardCard, GlowCard

class DashboardPage(QWidget):
    def __init__(self, current_user, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self._setup_ui()
        self._load_data()
        
        from core.signals import app_signals
        app_signals.payment_received.connect(self.refresh)
        app_signals.invoice_generated.connect(self.refresh)
    
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(24)
        
        # Header
        header_lbl = QLabel("Overview")
        header_lbl.setObjectName("page_title")
        main_layout.addWidget(header_lbl)
        
        # Row 1: 3 Prominent KPI Cards + Transfer Button
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(24)
        
        self.card_revenue = KPIDashboardCard("Today's Revenue", "Rs. 0.00", "💰", "#10B981")
        self.card_cash = KPIDashboardCard("Net Cash in Drawer", "Rs. 0.00", "💵", "#F59E0B")
        self.card_bank = KPIDashboardCard("Net Bank Balance", "Rs. 0.00", "🏦", "#3B82F6")
        
        row1_layout.addWidget(self.card_revenue)
        row1_layout.addWidget(self.card_cash)
        row1_layout.addWidget(self.card_bank)
        
        # Internal Transfer Button
        self.btn_transfer = QPushButton("🔄 Transfer Cash to Bank")
        self.btn_transfer.setStyleSheet("""
            QPushButton {
                background-color: #6366F1; color: white; font-size: 14px;
                font-weight: bold; padding: 15px 20px; border-radius: 8px;
            }
            QPushButton:hover { background-color: #4F46E5; }
        """)
        self.btn_transfer.clicked.connect(self._open_transfer_dialog)
        row1_layout.addWidget(self.btn_transfer, alignment=Qt.AlignRight | Qt.AlignVCenter)
        
        main_layout.addLayout(row1_layout)
        
        # Row 1b: Other KPIs
        row1b_layout = QHBoxLayout()
        row1b_layout.setSpacing(24)
        
        self.card_customers = KPIDashboardCard("Total Customers", "0", "👥", "#4F46E5")
        self.card_visas = KPIDashboardCard("Active Visas", "0", "🛃", "#F59E0B")
        self.card_flights = KPIDashboardCard("Upcoming Flights", "0", "✈️", "#0EA5E9")
        self.card_dues = KPIDashboardCard("Customer Dues", "Rs. 0.00", "⏳", "#EF4444")
        
        row1b_layout.addWidget(self.card_customers)
        row1b_layout.addWidget(self.card_visas)
        row1b_layout.addWidget(self.card_flights)
        row1b_layout.addWidget(self.card_dues)
        main_layout.addLayout(row1b_layout)
        
        # Row 2: Chart & Recent Activity
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(24)
        
        # --- Matplotlib Chart ---
        self.chart_card = GlowCard(glow_color="#FF2E93", glow_radius=15, alpha=30)
        chart_layout = QVBoxLayout(self.chart_card)
        chart_layout.setContentsMargins(20, 20, 20, 20)
        
        chart_title = QLabel("Revenue Trend")
        chart_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #E2E8F0;")
        chart_layout.addWidget(chart_title)
        
        # Figure setup
        self.figure = Figure(figsize=(6, 3), dpi=100)
        self.figure.patch.set_alpha(0.0) # Transparent background
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background: transparent;")
        
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor("none") # Transparent axis background
        
        # Remove top and right spines
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['bottom'].set_color('#4A4A5A')
        self.ax.spines['left'].set_color('#4A4A5A')
        self.ax.tick_params(axis='x', colors='#8B8B9E')
        self.ax.tick_params(axis='y', colors='#8B8B9E')
        
        self._plot_mock_data()
        
        chart_layout.addWidget(self.canvas)
        row2_layout.addWidget(self.chart_card, stretch=2)
        
        # --- Recent Activity Table ---
        activity_card = GlowCard()
        activity_layout = QVBoxLayout(activity_card)
        activity_layout.setContentsMargins(20, 20, 20, 20)
        
        activity_lbl = QLabel("Recent Activity")
        activity_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #E2E8F0;")
        activity_layout.addWidget(activity_lbl)
        
        self.activity_table = QTableWidget(0, 4)
        self.activity_table.setHorizontalHeaderLabels(["Time", "User", "Action", "Description"])
        self.activity_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.activity_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.activity_table.verticalHeader().setVisible(False)
        self.activity_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.activity_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.activity_table.setShowGrid(False)
        
        activity_layout.addWidget(self.activity_table)
        row2_layout.addWidget(activity_card, stretch=3)
        
        main_layout.addLayout(row2_layout)
        
    def _plot_mock_data(self):
        """Plot a neon pink line chart with gradient fill under it."""
        self.ax.clear()
        
        # Mock data
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
        revenue = [120000, 150000, 180000, 140000, 210000, 250000]
        x = np.arange(len(months))
        
        # Neon Pink Line
        line_color = '#FF2E93'
        self.ax.plot(x, revenue, color=line_color, linewidth=3, marker='o', markersize=6)
        
        # Fill between for glow effect
        self.ax.fill_between(x, revenue, alpha=0.15, color=line_color)
        
        self.ax.set_xticks(x)
        self.ax.set_xticklabels(months)
        
        # Restore spine colors
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['bottom'].set_color('#4A4A5A')
        self.ax.spines['left'].set_color('#4A4A5A')
        self.ax.tick_params(axis='x', colors='#8B8B9E')
        self.ax.tick_params(axis='y', colors='#8B8B9E')
        
        self.figure.tight_layout()
        self.canvas.draw()

    def _load_data(self):
        from viewmodels.dashboard_viewmodel import DashboardViewModel
        self.viewmodel = DashboardViewModel()
        self.viewmodel.kpis_updated.connect(self._on_kpis_updated)
        self.viewmodel.recent_activity_updated.connect(self._on_activity_updated)
        self.viewmodel.error_occurred.connect(self._on_error)
        
        self.viewmodel.load_dashboard_data()
            
    def _on_kpis_updated(self, kpis):
        self.card_revenue.set_value(f"Rs. {kpis.get('gross_sales', 0.0):,.2f}")
        self.card_cash.set_value(f"Rs. {kpis.get('cash_in_hand', 0.0):,.2f}")
        self.card_bank.set_value(f"Rs. {kpis.get('bank_balance', 0.0):,.2f}")
        
        self.card_customers.set_value(str(kpis.get('total_customers', 0)))
        self.card_visas.set_value(str(kpis.get('active_visas', 0)))
        self.card_flights.set_value(str(kpis.get('upcoming_flights', 0)))
        self.card_dues.set_value(f"Rs. {kpis.get('customer_dues', 0.0):,.2f}")
        
        # Store for dialog use
        self.current_cash = kpis.get('cash_in_hand', 0.0)

    def _open_transfer_dialog(self):
        from ui.pages.accounting.financial_dialogs import InternalTransferDialog
        cash = getattr(self, 'current_cash', 0.0)
        dialog = InternalTransferDialog(cash, self)
        if dialog.exec():
            self.refresh()

        
    def _on_activity_updated(self, activities):
        self.activity_table.setRowCount(0)
        for row, activity in enumerate(activities):
            self.activity_table.insertRow(row)
            
            time_item = QTableWidgetItem(format_datetime(activity.get("created_at")))
            time_item.setForeground(Qt.GlobalColor.gray)
            
            user_item = QTableWidgetItem(activity.get("username", ""))
            
            action_item = QTableWidgetItem(f"{activity.get('module')} - {activity.get('action')}")
            
            desc_item = QTableWidgetItem(activity.get("description", ""))
            
            self.activity_table.setItem(row, 0, time_item)
            self.activity_table.setItem(row, 1, user_item)
            self.activity_table.setItem(row, 2, action_item)
            self.activity_table.setItem(row, 3, desc_item)
        
    def _on_error(self, message):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.warning(self, "Dashboard Error", message)
            
    def refresh(self):
        if hasattr(self, 'viewmodel'):
            self.viewmodel.load_dashboard_data()
        else:
            self._load_data()
