import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QLabel, QStatusBar, QFrame, QPushButton, QMessageBox, QApplication, QLineEdit, QSizePolicy)
from PySide6.QtCore import Qt, QTimer, Signal, QPoint
from PySide6.QtGui import QKeySequence, QShortcut, QFont, QPixmap, QIcon
from core.signals import app_signals
from services.company_profile_service import CompanyProfileService

# Static imports to ensure PyInstaller bundles all pages
from ui.pages.dashboard.dashboard_page import DashboardPage
from ui.pages.customers.customer_list import CustomerListPage
from ui.pages.employees.employee_list import EmployeeListPage
from ui.pages.flights.flight_list import FlightListPage
from ui.pages.visa.visa_list import VisaListPage
from ui.pages.hotels.hotel_list import HotelListPage
from ui.pages.umrah.umrah_list import UmrahListPage
from ui.pages.hajj.hajj_list import HajjListPage
from ui.pages.transport.transport_list import TransportListPage
from ui.pages.accounting.accounts_page import AccountingPage
from ui.pages.accounting.reports_page import FinancialReportsPage
from ui.pages.settings.settings_page import SettingsPage
from ui.pages.vendors.vendor_list import VendorListPage
from ui.pages.tours.tour_list import TourListPage
from ui.pages.documents.documents_page import DocumentsPage

class PlaceholderPage(QWidget):
    def __init__(self, title):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_title = QLabel(title)
        lbl_title.setObjectName("lbl_title")
        lbl_title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_soon = QLabel("Coming Soon")
        lbl_soon.setObjectName("lbl_subtitle")
        lbl_soon.setFont(QFont("Segoe UI", 16))
        lbl_soon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_soon)

class MainWindow(QMainWindow):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self._pages: dict[str, QWidget] = {}
        self._current_module = 'dashboard'
        
        # Frameless Window Setup
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setMinimumSize(1200, 800)
        self.setWindowTitle("TAMS - Hamza Travels & Tours")
        
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logo", "logo.png")
        if os.path.exists(logo_path):
            self.setWindowIcon(QIcon(logo_path))
        
        self.drag_pos = QPoint()
        
        self._setup_ui()
        self._setup_shortcuts()
        self._setup_session_timer()
        self._apply_permissions()
        
        self.profile_service = CompanyProfileService()
        self._load_company_logo()
        app_signals.company_profile_updated.connect(self._load_company_logo)
        
        self.navigate_to('dashboard')
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Only allow dragging if clicking on the title bar area
            if event.position().y() < 60:
                self.drag_pos = event.globalPosition().toPoint()
                event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_pos:
            diff = event.globalPosition().toPoint() - self.drag_pos
            self.move(self.pos() + diff)
            self.drag_pos = event.globalPosition().toPoint()

    def _load_company_logo(self):
        profile = self.profile_service.get_profile()
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logo", "logo.png")
        
        if profile and profile.logo_data:
            pixmap = QPixmap()
            pixmap.loadFromData(profile.logo_data)
            scaled_pixmap = pixmap.scaled(180, 60, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.logo_icon.setPixmap(scaled_pixmap)
            self.logo_label.setText(profile.company_name or "Hamza Travels")
        elif os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            scaled_pixmap = pixmap.scaled(180, 60, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.logo_icon.setPixmap(scaled_pixmap)
            self.logo_label.setText(profile.company_name if profile else "Hamza Travels")
        else:
            self.logo_icon.setText("🚀")
            self.logo_icon.setStyleSheet("font-size: 32px; background: transparent;")
            self.logo_label.setText(profile.company_name if profile else "Hamza Travels")

    def mouseReleaseEvent(self, event):
        self.drag_pos = None
        event.accept()
    
    def _setup_ui(self):
        # Main central widget and layout (simulate a window frame)
        self.central_widget = QFrame()
        self.central_widget.setObjectName("MainWindowFrame")
        self.central_widget.setStyleSheet("QFrame#MainWindowFrame { background: #12121E; border: 1px solid #1C1C2D; border-radius: 12px; }")
        self.setCentralWidget(self.central_widget)
        
        # Overall vertical layout to include the custom title bar
        window_layout = QVBoxLayout(self.central_widget)
        window_layout.setContentsMargins(0, 0, 0, 0)
        window_layout.setSpacing(0)
        
        # --- Custom Title Bar ---
        self.title_bar = QFrame()
        self.title_bar.setObjectName("TitleBar")
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(20, 0, 0, 0)
        title_layout.setSpacing(0)
        
        app_title = QLabel("TAMS ERP")
        app_title.setStyleSheet("font-size: 11px; font-weight: bold; color: #8B8B9E;")
        title_layout.addWidget(app_title)
        title_layout.addStretch()
        
        # Window Controls
        btn_min = QPushButton("🗕")
        btn_min.setFixedSize(45, 40)
        btn_min.clicked.connect(self.showMinimized)
        
        btn_max = QPushButton("🗖")
        btn_max.setFixedSize(45, 40)
        btn_max.clicked.connect(lambda: self.showNormal() if self.isMaximized() else self.showMaximized())
        
        btn_close = QPushButton("✕")
        btn_close.setObjectName("btn_close")
        btn_close.setFixedSize(45, 40)
        btn_close.clicked.connect(self.close)
        
        for btn in [btn_min, btn_max, btn_close]:
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            title_layout.addWidget(btn)
            
        window_layout.addWidget(self.title_bar)
        
        # --- Main Layout Below Title Bar ---
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        window_layout.addLayout(main_layout)
        
        # --- Sidebar ---
        self.sidebar = QWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(250)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 10, 0, 20)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Sidebar Logo Area
        logo_frame = QFrame()
        logo_layout = QVBoxLayout(logo_frame)
        logo_layout.setContentsMargins(16, 8, 16, 8)
        
        self.logo_icon = QLabel()
        self.logo_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.logo_label = QLabel("Hamza Travels")
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #FFFFFF; background: transparent;")
        
        logo_sub = QLabel("Management System")
        logo_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_sub.setStyleSheet("font-size: 10px; color: #8B8B9E; background: transparent;")
        
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("border: none; border-top: 1px solid rgba(255,255,255,0.05); margin: 10px 0;")
        
        logo_layout.addWidget(self.logo_icon)
        logo_layout.addWidget(self.logo_label)
        logo_layout.addWidget(logo_sub)
        logo_layout.addWidget(divider)
        sidebar_layout.addWidget(logo_frame)
        
        # --- Middle Zone: Scrollable Navigation ---
        from PySide6.QtWidgets import QScrollArea
        from ui.components.modern_widgets import CollapsibleMenu
        
        self.nav_scroll = QScrollArea()
        self.nav_scroll.setWidgetResizable(True)
        self.nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.nav_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.nav_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        nav_container = QWidget()
        nav_container.setObjectName("SidebarNav")
        self.nav_layout = QVBoxLayout(nav_container)
        self.nav_layout.setContentsMargins(0, 0, 0, 0)
        self.nav_layout.setSpacing(5)
        self.nav_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.nav_buttons = {}

        # 1. Dashboard (Single)
        btn_dash = QPushButton("  🏠 Dashboard")
        btn_dash.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_dash.clicked.connect(lambda: self.navigate_to("dashboard"))
        self.nav_buttons["dashboard"] = btn_dash
        self.nav_layout.addWidget(btn_dash)
        
        btn_docs = QPushButton("  📂 Documents")
        btn_docs.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_docs.clicked.connect(lambda: self.navigate_to("documents"))
        self.nav_buttons["documents"] = btn_docs
        self.nav_layout.addWidget(btn_docs)
        
        # 2. CRM & HR (Collapsible)
        menu_crm = CollapsibleMenu("👥 CRM & HR")
        btn_customers = QPushButton("  👤 Customers")
        btn_customers.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_customers.clicked.connect(lambda: self.navigate_to("customers"))
        self.nav_buttons["customers"] = btn_customers
        menu_crm.add_item(btn_customers)
        
        btn_employees = QPushButton("  👥 Employees")
        btn_employees.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_employees.clicked.connect(lambda: self.navigate_to("employees"))
        self.nav_buttons["employees"] = btn_employees
        menu_crm.add_item(btn_employees)
        
        btn_vendors = QPushButton("  🤝 Vendors")
        btn_vendors.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_vendors.clicked.connect(lambda: self.navigate_to("vendors"))
        self.nav_buttons["vendors"] = btn_vendors
        menu_crm.add_item(btn_vendors)
        
        self.nav_layout.addWidget(menu_crm)
        
        # 3. Religious (Collapsible)
        menu_rel = CollapsibleMenu("🕋 Religious")
        btn_umrah = QPushButton("  🕋 Umrah")
        btn_umrah.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_umrah.clicked.connect(lambda: self.navigate_to("umrah"))
        self.nav_buttons["umrah"] = btn_umrah
        menu_rel.add_item(btn_umrah)
        
        btn_hajj = QPushButton("  🕌 Hajj")
        btn_hajj.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_hajj.clicked.connect(lambda: self.navigate_to("hajj"))
        self.nav_buttons["hajj"] = btn_hajj
        menu_rel.add_item(btn_hajj)
        self.nav_layout.addWidget(menu_rel)
        
        # 4. Services (Collapsible)
        menu_srv = CollapsibleMenu("✈️ Services")
        btn_flights = QPushButton("  ✈️ Flights")
        btn_flights.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_flights.clicked.connect(lambda: self.navigate_to("flights"))
        self.nav_buttons["flights"] = btn_flights
        menu_srv.add_item(btn_flights)
        
        btn_visas = QPushButton("  🛂 Visas")
        btn_visas.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_visas.clicked.connect(lambda: self.navigate_to("visas"))
        self.nav_buttons["visas"] = btn_visas
        menu_srv.add_item(btn_visas)
        
        btn_hotels = QPushButton("  🏨 Hotels")
        btn_hotels.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_hotels.clicked.connect(lambda: self.navigate_to("hotels"))
        self.nav_buttons["hotels"] = btn_hotels
        menu_srv.add_item(btn_hotels)
        
        btn_trans = QPushButton("  🚌 Transport")
        btn_trans.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_trans.clicked.connect(lambda: self.navigate_to("transport"))
        self.nav_buttons["transport"] = btn_trans
        menu_srv.add_item(btn_trans)
        
        btn_tours = QPushButton("  🌍 Tours")
        btn_tours.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_tours.clicked.connect(lambda: self.navigate_to("tours"))
        self.nav_buttons["tours"] = btn_tours
        menu_srv.add_item(btn_tours)
        
        self.nav_layout.addWidget(menu_srv)
        
        # 5. Finance (Collapsible)
        menu_fin = CollapsibleMenu("📊 Finance")
        btn_inv = QPushButton("  🧾 Invoices")
        btn_inv.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_inv.clicked.connect(lambda: self.navigate_to("invoices"))
        self.nav_buttons["invoices"] = btn_inv
        menu_fin.add_item(btn_inv)
        
        btn_rep = QPushButton("  📊 Reports")
        btn_rep.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_rep.clicked.connect(lambda: self.navigate_to("reports"))
        self.nav_buttons["reports"] = btn_rep
        menu_fin.add_item(btn_rep)
        self.nav_layout.addWidget(menu_fin)
        
        self.nav_scroll.setWidget(nav_container)
        sidebar_layout.addWidget(self.nav_scroll)
        
        # --- Bottom Zone: Pinned User Profile & Settings ---
        bottom_zone = QFrame()
        bottom_zone_layout = QVBoxLayout(bottom_zone)
        bottom_zone_layout.setContentsMargins(0, 0, 0, 0)
        bottom_zone_layout.setSpacing(5)
        
        # Settings Button
        btn_settings = QPushButton("  ⚙️ Settings")
        btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_settings.clicked.connect(lambda: self.navigate_to("settings"))
        self.nav_buttons["settings"] = btn_settings
        bottom_zone_layout.addWidget(btn_settings)

        # User Info Badge
        user_badge = QFrame()
        user_badge.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.03);
                border-radius: 12px;
                margin: 4px 12px;
                border: 1px solid rgba(255,255,255,0.05);
            }
        """)
        badge_layout = QHBoxLayout(user_badge)
        badge_layout.setContentsMargins(10, 10, 10, 10)
        
        avatar_lbl = QLabel(getattr(self.current_user, 'username', 'U')[:1].upper())
        avatar_lbl.setFixedSize(36, 36)
        avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar_lbl.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF512F, stop:1 #DD2476); "
            "color: white; border-radius: 18px; font-weight: bold; font-size: 14px; border: none;"
        )
        
        user_info_layout = QVBoxLayout()
        user_info_layout.setSpacing(2)
        uname_lbl = QLabel(getattr(self.current_user, 'username', 'Unknown'))
        uname_lbl.setStyleSheet("color: #FFFFFF; font-size: 12px; font-weight: bold; background: transparent; border: none;")
        urole_lbl = QLabel(getattr(self.current_user, 'role', 'Employee'))
        urole_lbl.setStyleSheet("color: #8B8B9E; font-size: 10px; background: transparent; border: none;")
        user_info_layout.addWidget(uname_lbl)
        user_info_layout.addWidget(urole_lbl)
        
        badge_layout.addWidget(avatar_lbl)
        badge_layout.addLayout(user_info_layout)
        bottom_zone_layout.addWidget(user_badge)
        
        # Logout button
        logout_btn = QPushButton("  🚪  Sign Out")
        logout_btn.setObjectName("btn_danger")
        logout_btn.clicked.connect(self.logout)
        logout_btn.setStyleSheet("margin: 5px 12px 10px 12px;")
        bottom_zone_layout.addWidget(logout_btn)
        
        sidebar_layout.addWidget(bottom_zone)
        
        # --- Content Area (Top Bar + Stacked Widget) ---
        content_wrapper = QWidget()
        content_layout = QVBoxLayout(content_wrapper)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Top Bar
        self.topbar = QFrame()
        self.topbar.setObjectName("topbar")
        topbar_layout = QHBoxLayout(self.topbar)
        topbar_layout.setContentsMargins(30, 0, 30, 0)
        
        self.breadcrumb_label = QLabel("Dashboard")
        self.breadcrumb_label.setObjectName("lbl_title")
        topbar_layout.addWidget(self.breadcrumb_label)
        
        topbar_layout.addStretch()
        
        # Search Bar
        self.search_input = QLineEdit()
        self.search_input.setObjectName("search_box")
        self.search_input.setPlaceholderText("🔍  Search PNR, Customer, or Invoice...")
        self.search_input.setFixedWidth(300)
        topbar_layout.addWidget(self.search_input)
        
        topbar_layout.addSpacing(20)
        
        # Top right action buttons (notifications etc)
        notif_btn = QPushButton("🔔")
        notif_btn.setFixedSize(40, 40)
        notif_btn.setStyleSheet("border-radius: 20px; font-size: 16px; background: rgba(255,255,255,0.05);")
        topbar_layout.addWidget(notif_btn)
        
        content_layout.addWidget(self.topbar)
        
        # Page Container to provide baseline margin to all pages
        page_container = QWidget()
        page_layout = QVBoxLayout(page_container)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)
        
        # Stacked Widget
        self.stacked_widget = QStackedWidget()
        page_layout.addWidget(self.stacked_widget)
        
        content_layout.addWidget(page_container)
        
        # Add to main layout
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(content_wrapper)
        
        # Status Bar
        self.statusBar = QStatusBar()
        self.statusBar.setStyleSheet("background: #0F0F1A; color: #8B8B9E; border-top: 1px solid #1C1C2D;")
        window_layout.addWidget(self.statusBar)
        self.statusBar.showMessage("Ready")
        
    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+Q"), self, self.close)
    
    def _apply_permissions(self):
        from core.permissions import has_permission, Modules, Actions
        
        # Map nav button keys to module constants
        nav_module_map = {
            "dashboard": Modules.DASHBOARD,
            "customers": Modules.CUSTOMERS,
            "employees": Modules.EMPLOYEES,
            "umrah": Modules.UMRAH,
            "hajj": Modules.HAJJ,
            "flights": Modules.FLIGHTS,
            "visas": Modules.VISA,
            "hotels": Modules.HOTELS,
            "transport": Modules.TRANSPORT,
            "tours": Modules.TOURS,
            "invoices": Modules.ACCOUNTING,
            "reports": Modules.REPORTS,
            "settings": Modules.SETTINGS
        }
        
        for nav_key, btn in self.nav_buttons.items():
            mod = nav_module_map.get(nav_key)
            if mod:
                if not has_permission(self.current_user, mod, Actions.VIEW):
                    btn.hide()
    
    def navigate_to(self, module_name: str):
        self._current_module = module_name
        
        # Update sidebar active state
        for mod_id, btn in self.nav_buttons.items():
            if mod_id == module_name:
                btn.setProperty("active", True)
            else:
                btn.setProperty("active", False)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            
        # Lazy-load the module page
        page = self._get_or_create_page(module_name)
        
        if self.stacked_widget.indexOf(page) == -1:
            self.stacked_widget.addWidget(page)
            
        self.stacked_widget.setCurrentWidget(page)
        
        # Update breadcrumb
        display_name = module_name.capitalize()
        self.breadcrumb_label.setText(display_name)
    
    def _get_or_create_page(self, module_name: str) -> QWidget:
        if module_name not in self._pages:
            if module_name == 'dashboard':
                self._pages[module_name] = DashboardPage(self.current_user)
            elif module_name == 'customers':
                self._pages[module_name] = CustomerListPage(self.current_user)
            elif module_name == 'employees':
                self._pages[module_name] = EmployeeListPage(self.current_user)
            elif module_name == 'flights':
                self._pages[module_name] = FlightListPage(self.current_user)
            elif module_name == 'visas':
                self._pages[module_name] = VisaListPage(self.current_user)
            elif module_name == 'hotels':
                self._pages[module_name] = HotelListPage(self.current_user)
            elif module_name == 'umrah':
                self._pages[module_name] = UmrahListPage(self.current_user)
            elif module_name == 'hajj':
                self._pages[module_name] = HajjListPage(self.current_user)
            elif module_name == 'transport':
                self._pages[module_name] = TransportListPage(self.current_user)
            elif module_name == 'invoices':
                self._pages[module_name] = AccountingPage(self.current_user)
            elif module_name == 'reports':
                self._pages[module_name] = FinancialReportsPage(self.current_user)
            elif module_name == 'settings':
                self._pages[module_name] = SettingsPage(self.current_user)
            elif module_name == 'vendors':
                self._pages[module_name] = VendorListPage(self.current_user)
            elif module_name == 'tours':
                self._pages[module_name] = TourListPage(self.current_user)
            elif module_name == 'documents':
                self._pages[module_name] = DocumentsPage(self.current_user)
            else:
                self._pages[module_name] = PlaceholderPage(module_name.capitalize())
                
            if hasattr(self._pages[module_name], 'viewmodel') and hasattr(self._pages[module_name].viewmodel, 'success_occurred'):
                self._pages[module_name].viewmodel.success_occurred.connect(
                    lambda msg: self.statusBar.showMessage(msg, 4000)
                )
                
        return self._pages[module_name]
    
    def _setup_session_timer(self):
        self.session_timer = QTimer(self)
        self.session_timer.timeout.connect(self._check_session)
        self.session_timer.start(60000)
        self.session_time_left = 30
    
    def _check_session(self):
        self.session_time_left -= 1
        if self.session_time_left <= 0:
            self.session_timer.stop()
            QMessageBox.warning(self, "Session Expired", "Your session has expired. Please log in again.")
            self.logout()
    
    def logout(self):
        reply = QMessageBox.question(
            self, "Confirm Logout",
            "Are you sure you want to sign out?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
            
        self.session_timer.stop()
        self.close()
        
        from ui.windows.login_window import LoginWindow
        from ui.windows.main_window import MainWindow
        login_window = LoginWindow()
        
        _state = {"main": None}
        
        def on_login(user):
            login_window.close()
            main_window = MainWindow(user)
            _state["main"] = main_window
            main_window.show()
            
        login_window.login_successful.connect(on_login)
        login_window.show()
