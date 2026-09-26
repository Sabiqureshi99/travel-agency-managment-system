class DashboardPage(QWidget):
13:     def __init__(self, current_user, parent=None):
14:         super().__init__(parent)
15:         self.current_user = current_user
16:         self._setup_ui()
17:         self._load_data()
18:     
19:     def _setup_ui(self):
20:         main_layout = QVBoxLayout(self)
21:         main_layout.setContentsMargins(30, 30, 30, 30)
22:         main_layout.setSpacing(24)
23:         
24:         # Header
25:         header_lbl = QLabel("Overview")
26:         header_lbl.setObjectName("page_title")
27:         main_layout.addWidget(header_lbl)
28:         
29:         # Row 1: 4 KPIDashboardCards
30:         row1_layout = QHBoxLayout()
31:         row1_layout.setSpacing(24)
32:         
33:         self.card_revenue = KPIDashboardCard("Total Revenue", "Rs. 0.00", "ð°", "#10B981")
34:         self.card_customers = KPIDashboardCard("Total Customers", "0", "ð¥", "#4F46E5")
35:         self.card_visas = KPIDashboardCard("Active Visas", "0", "ð", "#F59E0B")
36:         self.card_flights = KPIDashboardCard("Upcoming Flights", "0", "âï¸", "#0EA5E9")
37:         
38:         row1_layout.addWidget(self.card_revenue)
39:         row1_layout.addWidget(self.card_customers)
40:         row1_layout.addWidget(self.card_visas)
41:         row1_layout.addWidget(self.card_flights)
42:         main_layout.addLayout(row1_layout)
43:         
44:         # Row 2: Chart & Recent Activity
45:         row2_layout = QHBoxLayout()
46:         row2_layout.setSpacing(24)
47:         
48:         # --- Matplotlib Chart ---
49:         self.chart_card = GlowCard(glow_color="#FF2E93", glow_radius=15, alpha=30)
50:         chart_layout = QVBoxLayout(self.chart_card)
51:         chart_layout.setContentsMargins(20, 20, 20, 20)
52:         
53:         chart_title = QLabel("Revenue Trend")
54:         chart_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #E2E8F0;")
55:         chart_layout.addWidget(chart_title)
56:         
57:         # Figure setup
58:         self.figure = Figure(figsize=(6, 3), dpi=100)
59:         self.figure.patch.set_alpha(0.0) # Transparent background
60:         self.canvas = FigureCanvas(self.figure)
61:         self.canvas.setStyleSheet("background: transparent;")
62:         
63:         self.ax = self.figure.add_subplot(111)
64:         self.ax.set_facecolor("none") # Transparent axis background
65:         
66:         # Remove top and right spines
67:         self.ax.spines['top'].set_visible(False)
68:         self.ax.spines['right'].set_visible(False)
69:         self.ax.spines['bottom'].set_color('#4A4A5A')
70:         self.ax.spines['left'].set_color('#4A4A5A')
71:         self.ax.tick_params(axis='x', colors='#8B8B9E')
72:         self.ax.tick_params(axis='y', colors='#8B8B9E')
73:         
74:         self._plot_mock_data()
75:         
76:         chart_layout.addWidget(self.canvas)
77:         row2_layout.addWidget(self.chart_card, stretch=2)
78:         
79:         # --- Recent Activity Table ---
80:         activity_card = GlowCard()
81:         activity_layout = QVBoxLayout(activity_card)
82:         activity_layout.setContentsMargins(20, 20, 20, 20)
83:         
84:         activity_lbl = QLabel("Recent Activity")
85:         activity_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #E2E8F0;")
86:         activity_layout.addWidget(activity_lbl)
87:         
88:         self.activity_table = QTableWidget(0, 4)
89:         self.activity_table.setHorizontalHeaderLabels(["Time", "User", "Action", "Description"])
90:         self.activity_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
91:         self.activity_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
92:         self.activity_table.verticalHeader().setVisible(False)
93:         self.activity_table.setEditTriggers(QTableWidget.NoEditTriggers)
94:         self.activity_table.setSelectionBehavior(QTableWidget.SelectRows)
95:         self.activity_table.setShowGrid(False)
96:         
97:         activity_layout.addWidget(self.activity_table)
98:         row2_layout.addWidget(activity_card, stretch=3)
99:         
100:         main_layout.addLayout(row2_layout)
101:         
102:     def _plot_mock_data(self):
103:         """Plot a neon pink line chart with gradient fill under it."""
104:         self.ax.clear()
105:         
106:         # Mock data
107:         months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
108:         revenue = [120000, 150000, 180000, 140000, 210000, 250000]
109:         x = np.arange(len(months))
110:         
111:         # Neon Pink Line
112:         line_color = '#FF2E93'
113:         self.ax.plot(x, revenue, color=line_color, linewidth=3, marker='o', markersize=6)
114:         
115:         # Fill between for glow effect
116:         self.ax.fill_between(x, revenue, alpha=0.15, color=line_color)
117:         
118:         self.ax.set_xticks(x)
119:         self.ax.set_xticklabels(months)
120:         
121:         # Restore spine colors
122:         self.ax.spines['top'].set_visible(False)
123:         self.ax.spines['right'].set_visible(False)
124:         self.ax.spines['bottom'].set_color('#4A4A5A')
125:         self.ax.spines['left'].set_color('#4A4A5A')
126:         self.ax.tick_params(axis='x', colors='#8B8B9E')
127:         self.ax.tick_params(axis='y', colors='#8B8B9E')
128:         
129:         self.figure.tight_layout()
130:         self.canvas.draw()
131: 
132:     def _load_data(self):
133:         from viewmodels.dashboard_viewmodel import DashboardViewModel
134:         self.viewmodel = DashboardViewModel()
135:         self.viewmodel.kpis_updated.connect(self._on_kpis_updated)
136:         self.viewmodel.recent_activity_updated.connect(self._on_activity_updated)
137:         self.viewmodel.error_occurred.connect(self._on_error)
138:         
139:         self.viewmodel.load_dashboard_data()
140:             
141:     def _on_kpis_updated(self, kpis):
142:         self.card_revenue.set_value(format_currency(kpis.get("total_revenue", 0.0)))
143:         self.card_customers.set_value(str(kpis.get("total_customers", 0)))
144:         self.card_visas.set_value(str(kpis.get("active_visas", 0)))
145:         self.card_flights.set_value(str(kpis.get("upcoming_flights", 0)))
146:         
147:     def _on_activity_updated(self, activities):
148:         self.activity_table.setRowCount(0)
149:         for row, activity in enumerate(activities):
150:             self.activity_table.insertRow(row)
151:             
152:             time_item = QTableWidgetItem(format_datetime(activity.get("created_at")))
153:             time_item.setForeground(Qt.GlobalColor.gray)
154:             
155:             user_item = QTableWidgetItem(activity.get("username", ""))
156:             
157:             action_item = QTableWidgetItem(f"{activity.get('module')} - {activity.get('action')}")
158:             
159:             desc_item = QTableWidgetItem(activity.get("description", ""))
160:             
161:             self.activity_table.setItem(row, 0, time_item)
162:             self.activity_table.setItem(row, 1, user_item)
163:             self.activity_table.setItem(row, 2, action_item)
164:             self.activity_table.setItem(row, 3, desc_item)
165:         
166:     def _on_error(self, message):
167:         from PySide6.QtWidgets import QMessageBox
168:         QMessageBox.warning(self, "Dashboard Error", message)
169:             
170:     def refresh(self):
171:         if hasattr(self, 'viewmodel'):
172:             self.viewmodel.load_dashboard_data()
173:         else:
174:             self._load_data()
175: 
