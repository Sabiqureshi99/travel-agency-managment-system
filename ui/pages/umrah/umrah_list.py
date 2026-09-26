from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QTableWidget, QTableWidgetItem, QTabWidget, QMessageBox, QHeaderView,
                               QScrollArea, QGridLayout, QLabel, QFrame, QSizePolicy, QDialog, QMenu, QLineEdit, QAbstractItemView)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QAction
from viewmodels.umrah_viewmodel import UmrahViewModel
from ui.pages.umrah.template_builder import TemplateBuilderDialog
from ui.pages.umrah.unified_booking_wizard_ui import UnifiedBookingWizardUI
from config.database import get_session
from models.umrah import CustomUmrahBooking
from models.accounting import Invoice
from services.invoice_generator import InvoiceGenerator
from utils.pdf_generator import VoucherBuilder
import os

class TemplateCard(QFrame):
    def __init__(self, template, pricing_list, parent_page=None):
        super().__init__()
        self.template = template
        self.pricing_list = pricing_list
        self.parent_page = parent_page
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        
        # Modern OTA style card
        self.setStyleSheet("""
            QFrame {
                background-color: #1A1D2E;
                border-radius: 12px;
                border: 1px solid #2A2D3E;
                margin: 8px;
            }
            QFrame:hover {
                border: 1.5px solid #4F46E5;
                background-color: #1E2135;
            }
            QLabel {
                border: none;
                margin: 0;
            }
        """)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(180)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)
        
        # Top section: Title and Rating
        header_layout = QHBoxLayout()
        header_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        title = QLabel(template.name)
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #FFFFFF;")
        
        star_lbl = QLabel(f"{'★' * int(template.star_rating)}")
        star_lbl.setFont(QFont("Segoe UI", 14))
        star_lbl.setStyleSheet("color: #F59E0B; font-weight: bold;")
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(star_lbl)
        main_layout.addLayout(header_layout)
        
        # Middle section: Highlights
        details_layout = QHBoxLayout()
        duration_lbl = QLabel(f"🌙 {template.total_days} Days / {template.total_nights} Nights")
        duration_lbl.setStyleSheet("color: #818CF8; font-weight: bold; font-size: 13px;")
        details_layout.addWidget(duration_lbl)
        details_layout.addStretch()
        
        btn_edit = QPushButton("Edit")
        btn_edit.setObjectName("btn_secondary")
        btn_edit.setFixedHeight(32)
        btn_edit.clicked.connect(self._on_edit)
        
        btn_delete = QPushButton("Delete")
        btn_delete.setObjectName("btn_danger")
        btn_delete.setFixedHeight(32)
        btn_delete.clicked.connect(self._on_delete)
        
        details_layout.addWidget(btn_edit)
        details_layout.addWidget(btn_delete)
        
        main_layout.addLayout(details_layout)
        
        hotels_lbl = QLabel(f"🕋 <b>Makkah:</b> {template.makkah_hotel or 'N/A'} ({template.makkah_nights}N)<br>"
                            f"🕌 <b>Medinah:</b> {template.medinah_hotel or 'N/A'} ({template.medinah_nights}N)")
        hotels_lbl.setStyleSheet("color: #C4CDE8; font-size: 13px; line-height: 1.5;")
        hotels_lbl.setWordWrap(True)
        main_layout.addWidget(hotels_lbl)
        
        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("background-color: #2A2D3E; margin-top: 5px; margin-bottom: 5px;")
        main_layout.addWidget(divider)
        
        # Bottom section: Pricing Blocks
        price_layout = QHBoxLayout()
        price_layout.setSpacing(10)
        
        prices = {"Double": "N/A", "Triple": "N/A", "Quad": "N/A"}
        for p in pricing_list:
            prices[p.room_type] = f"{template.currency} {float(p.price_per_person):,.0f}"
            
        for r_type in ["Double", "Triple", "Quad"]:
            p_block = QFrame()
            p_block.setStyleSheet("""
                QFrame {
                    background-color: rgba(79, 70, 229, 0.1);
                    border: 1px solid rgba(79, 70, 229, 0.3);
                    border-radius: 6px;
                    padding: 8px;
                }
            """)
            p_layout = QVBoxLayout(p_block)
            p_layout.setContentsMargins(5, 5, 5, 5)
            p_layout.setSpacing(2)
            p_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            rlbl = QLabel(r_type)
            rlbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            rlbl.setStyleSheet("color: #8892B0;")
            rlbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            plbl = QLabel(prices[r_type])
            plbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            plbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            plbl.setStyleSheet("color: #10B981;")
            
            p_layout.addWidget(rlbl)
            p_layout.addWidget(plbl)
            price_layout.addWidget(p_block)
            
        main_layout.addLayout(price_layout)

    def _on_edit(self):
        if self.parent_page:
            self.parent_page._edit_template(self.template, self.pricing_list)

    def _on_delete(self):
        if self.parent_page:
            self.parent_page._delete_template(self.template)


class CheckServicesDialog(QDialog):
    def __init__(self, booking_id: str, parent=None, list_page=None):
        super().__init__(parent)
        self.booking_id = booking_id
        self.list_page = list_page   # reference to UmrahListPage for refresh
        self.setWindowTitle("Check Services")
        self.setMinimumSize(750, 560)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        self.header_frame = QFrame()
        self.header_frame.setObjectName("card_frame")
        self.header_layout = QVBoxLayout(self.header_frame)
        self.header_layout.setContentsMargins(15, 12, 15, 12)
        
        self.tabs = QTabWidget()
        
        # --- Action buttons bar ---
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(10)
        
        btn_edit = QPushButton("✏️  Edit Booking")
        btn_edit.setObjectName("btn_warning")
        btn_edit.setMinimumHeight(40)
        btn_edit.setMinimumWidth(130)
        btn_edit.clicked.connect(self._open_edit_booking)
        
        btn_master_inv = QPushButton("🖨  Print Master Invoice")
        btn_master_inv.setObjectName("btn_primary")
        btn_master_inv.setShortcut("Return")
        btn_master_inv.clicked.connect(lambda checked=False: self._print_invoice(True))
        
        btn_item_inv = QPushButton("📋  Print Itemized Invoice")
        btn_item_inv.setObjectName("btn_secondary")
        btn_item_inv.clicked.connect(lambda checked=False: self._print_invoice(False))
        
        btn_voucher = QPushButton("🎟  Print Voucher")
        btn_voucher.clicked.connect(self._print_voucher)
        
        bottom_layout.addWidget(btn_edit)
        bottom_layout.addStretch()
        bottom_layout.addWidget(btn_master_inv)
        bottom_layout.addWidget(btn_item_inv)
        bottom_layout.addWidget(btn_voucher)
        
        main_layout.addWidget(self.header_frame)
        main_layout.addWidget(self.tabs, 1)
        main_layout.addLayout(bottom_layout)
        
        self._load_data()
        
    def _load_data(self):
        try:
            with get_session() as session:
                umrah = session.get(CustomUmrahBooking, self.booking_id)
                if not umrah:
                    QMessageBox.warning(self, "Error", "Booking not found.")
                    self.reject()
                    return
                
                # Header Summary
                cust_name = umrah.customer.full_name if umrah.customer else "CASH CUSTOMER"
                cust_pass = umrah.customer.passport_number if umrah.customer else "N/A"
                pkg_name = umrah.template.name if umrah.template else "Custom Umrah"
                
                self.header_layout.addWidget(QLabel(f"<b>Customer:</b> {cust_name} (Passport: {cust_pass})"))
                self.header_layout.addWidget(QLabel(f"<b>Reference:</b> {umrah.booking_number} | <b>Package:</b> {pkg_name}"))
                self.header_layout.addWidget(QLabel(f"<b>Grand Total:</b> {umrah.final_total_price:,.2f}"))
                
                # Flights Tab
                f_tab = QWidget()
                f_layout = QVBoxLayout(f_tab)
                if not umrah.flights:
                    f_layout.addWidget(QLabel("No flights attached."))
                else:
                    for f in umrah.flights:
                        f_layout.addWidget(QLabel(f"✈ {f.leg_type} | {f.airline} ({f.flight_number}) | {f.origin} to {f.destination} | Date: {f.departure_date} | PNR: {f.pnr}"))
                f_layout.addStretch()
                self.tabs.addTab(f_tab, "Flights")
                
                # Hotels Tab
                h_tab = QWidget()
                h_layout = QVBoxLayout(h_tab)
                if not umrah.hotels:
                    h_layout.addWidget(QLabel("No hotels attached."))
                else:
                    for h in umrah.hotels:
                        h_layout.addWidget(QLabel(f"🏨 {h.city} | {h.hotel_name_override or h.notes} | {h.check_in_date} to {h.check_out_date} | {h.room_type} | {h.num_rooms} Room(s)"))
                h_layout.addStretch()
                self.tabs.addTab(h_tab, "Hotels")
                
                # Transport Tab
                t_tab = QWidget()
                t_layout = QVBoxLayout(t_tab)
                if not umrah.transport_details:
                    t_layout.addWidget(QLabel("No transport attached."))
                else:
                    tds = umrah.transport_details
                    if isinstance(tds, dict):
                        tds = [tds]
                    for td in tds:
                        t_route = td.get('service_route', 'Unknown Route')
                        t_type = td.get('type', 'Standard')
                        t_pickup = td.get('pickup_date', '')
                        t_driver = td.get('contact_person', '')
                        t_tn = td.get('tn_number', '')
                        t_layout.addWidget(QLabel(f"🚌 {t_route} | {t_type} | TN: {t_tn} | Pickup: {t_pickup} | Driver: {t_driver}"))
                t_layout.addStretch()
                self.tabs.addTab(t_tab, "Transport")
                
                # Visa Tab
                v_tab = QWidget()
                v_layout = QVBoxLayout(v_tab)
                if not umrah.visas:
                    v_layout.addWidget(QLabel("No visa attached."))
                else:
                    for v in umrah.visas:
                        v_layout.addWidget(QLabel(f"🛂 {v.visa_type} | Status: {v.status}"))
                v_layout.addStretch()
                self.tabs.addTab(v_tab, "Visa")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            self.reject()

    def _open_edit_booking(self):
        """Close this dialog and open the Unified Booking Wizard in edit mode."""
        self.accept()  # close Check Services first
        wizard = UnifiedBookingWizardUI(parent=self.parent())
        wizard.setWindowModality(Qt.WindowModality.ApplicationModal)
        wizard.load_booking(self.booking_id)      # populate all fields from DB
        wizard.go_to_checkout()                   # jump straight to checkout summary
        wizard.exec()
        # Refresh the list page so updated data shows immediately
        if self.list_page:
            self.list_page.refresh()

    def _print_invoice(self, is_summary):
        try:
            with get_session() as session:
                umrah = session.get(CustomUmrahBooking, self.booking_id)
                invoice = session.query(Invoice).filter_by(reference_id=umrah.id).first()
                if not invoice:
                    QMessageBox.warning(self, "No Invoice", "No invoice found for this booking.")
                    return
                
                pkg_name = umrah.template.name if umrah.template else "Custom Umrah"
                os.makedirs("invoices", exist_ok=True)
                suffix = "Master" if is_summary else "Itemized"
                path = os.path.abspath(f"invoices/Invoice_{invoice.invoice_number}_{suffix}.pdf")
                
                if is_summary:
                    InvoiceGenerator.generate_invoice_pdf(invoice, path, is_package_summary=True, package_name=pkg_name)
                else:
                    InvoiceGenerator.generate_umrah_group_invoice_pdf(invoice, path, umrah_booking=umrah)
                
                if os.path.exists(path):
                    os.startfile(path)
        except Exception as e:
            QMessageBox.critical(self, "Print Error", str(e))

    def _print_voucher(self):
        try:
            with get_session() as session:
                umrah = session.get(CustomUmrahBooking, self.booking_id)
                if not umrah:
                    return
                
                customer = umrah.customer
                pkg_name = umrah.template.name if umrah.template else "Custom Umrah"
                import datetime
                now = datetime.datetime.now()
                
                data = {
                    'voucher_no': f"HV-{umrah.booking_number}",
                    'issue_date': QDate.currentDate().toString("dd/MM/yyyy"),
                    'pkg_category': pkg_name,
                    'print_dt': now.strftime("%d-%m-%Y %H:%M:%S"),
                    'branch_office': 'HAMZA NAWABSHAH - UMRAH',
                    'passengers': [],
                    'accommodation': [],
                    'transport': [],
                    'flights': []
                }
                
                # Passengers
                if umrah.pilgrims:
                    for p in umrah.pilgrims:
                        data['passengers'].append({
                            'name': p.full_name,
                            'passport': p.passport_number or 'N/A',
                            'group': p.group_no or (customer.full_name if customer else 'N/A')
                        })
                else:
                    data['passengers'].append({
                        'name': customer.full_name if customer else 'N/A',
                        'passport': customer.passport_number if (customer and customer.passport_number) else 'N/A',
                        'group': customer.full_name if customer else 'N/A'
                    })
                    
                # Accommodation
                for h in umrah.hotels:
                    nights = (h.check_out_date - h.check_in_date).days if h.check_in_date and h.check_out_date else 0
                    data['accommodation'].append({
                        'city': h.city,
                        'hn': h.hn_number or str(len(data['accommodation']) + 1),
                        'hotel_name': h.hotel_name_override or h.notes or '',
                        'room': h.num_rooms or 1,
                        'room_type': h.room_type or 'DOUBLE',
                        'check_in': h.check_in_date.strftime("%d/%m/%Y") if h.check_in_date else '',
                        'check_out': h.check_out_date.strftime("%d/%m/%Y") if h.check_out_date else '',
                        'nights': nights,
                        'reservation_name': h.reservation_name or ''
                    })
                    
                # Transport
                if umrah.transport_details:
                    tds = umrah.transport_details
                    if isinstance(tds, dict):
                        tds = [tds]
                    for td in tds:
                        if not td.get('exclude_invoice'):
                            pickup = td.get('pickup_date')
                            if hasattr(pickup, 'strftime'):
                                pickup_str = pickup.strftime("%d/%m/%Y")
                            else:
                                pickup_str = str(pickup) if pickup else datetime.date.today().strftime("%d/%m/%Y")
                                
                            data['transport'].append({
                                'tn': td.get('tn_number') or '1',
                                'service': td.get('service_route') or 'UMRAH ROUTE',
                                'vehicle': td.get('type') or '',
                                'pickup_date': pickup_str,
                                'contact': td.get('contact_person') or 'N/A',
                                'ref_no': td.get('booking_ref') or f"TR-{umrah.booking_number}"
                            })
                            
                # Flights
                for f in umrah.flights:
                    data['flights'].append({
                        'pnr': f.pnr or 'TBA',
                        'date': f.departure_date.strftime("%d/%m/%Y") if f.departure_date else datetime.date.today().strftime("%d/%m/%Y"),
                        'flight': f.flight_number or f.airline,
                        'from': f.origin,
                        'to': f.destination,
                        'dep': f.departure_time or 'TBA',
                        'arr': f.arrival_time or 'TBA'
                    })
                
                os.makedirs("vouchers", exist_ok=True)
                pdf_path = os.path.abspath(f"vouchers/Voucher_{umrah.booking_number}.pdf")
                
                builder = VoucherBuilder(data, pdf_path)
                builder.generate()
                
                if os.path.exists(pdf_path):
                    os.startfile(pdf_path)
        except Exception as e:
            QMessageBox.critical(self, "Voucher Error", str(e))

class UmrahListPage(QWidget):
    def __init__(self, current_user, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.viewmodel = UmrahViewModel()
        
        self.viewmodel.templates_loaded.connect(self._on_templates_loaded)
        self.viewmodel.bookings_loaded.connect(self._on_bookings_loaded)
        self.viewmodel.pricing_loaded.connect(self._on_pricing_fetched_for_card)
        self.viewmodel.error_occurred.connect(self._on_error)
        
        # Connect global signals for background refresh
        from core.signals import app_signals
        app_signals.umrah_checkout_completed.connect(self.refresh)
        
        self.template_cache = []
        self.pricing_cache = {} # template_id -> pricing list
        self.pending_pricing_requests = 0
        
        self.current_template_skip = 0
        self.current_booking_skip = 0
        self.limit = 50
        
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        header_layout = QHBoxLayout()
        header = QLabel("Umrah Module")
        header.setStyleSheet("font-size: 24px; font-weight: bold; padding: 16px;")
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search templates or custom bookings...")
        self.search_input.setFixedWidth(300)
        self.search_input.textChanged.connect(self.refresh)
        
        header_layout.addWidget(header)
        header_layout.addStretch()
        header_layout.addWidget(self.search_input)
        layout.addLayout(header_layout)
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Templates Tab (Card Catalog)
        templates_tab = QWidget()
        templates_layout = QVBoxLayout(templates_tab)
        templates_layout.setSpacing(15)
        
        btn_layout1 = QHBoxLayout()
        add_template_btn = QPushButton("Create Master Template")
        add_template_btn.setObjectName("btn_primary")
        add_template_btn.setShortcut("Return")
        add_template_btn.clicked.connect(self._create_template)
        btn_layout1.addStretch()
        btn_layout1.addWidget(add_template_btn)
        templates_layout.addLayout(btn_layout1)
        
        # Scroll Area for Cards
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.cards_container = QWidget()
        self.cards_container.setStyleSheet("background: transparent;")
        self.cards_layout = QGridLayout(self.cards_container)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.cards_layout.setSpacing(10)
        
        self.scroll_area.setWidget(self.cards_container)
        templates_layout.addWidget(self.scroll_area)
        
        # Pagination for Templates
        from ui.components.pagination import PaginationWidget
        self.template_pagination = PaginationWidget()
        self.template_pagination.page_changed.connect(self._on_template_page_changed)
        templates_layout.addWidget(self.template_pagination)
        
        self.tabs.addTab(templates_tab, "Package Catalog")
        
        # Custom Bookings Tab
        bookings_tab = QWidget()
        bookings_layout = QVBoxLayout(bookings_tab)
        bookings_layout.setSpacing(15)
        
        btn_layout2 = QHBoxLayout()
        btn_layout2.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        add_booking_btn = QPushButton("Open Booking Pipeline")
        add_booking_btn.setObjectName("btn_primary")
        add_booking_btn.setShortcut("Return")
        add_booking_btn.clicked.connect(self._add_booking)
        btn_layout2.addStretch()
        btn_layout2.addWidget(add_booking_btn)
        bookings_layout.addLayout(btn_layout2)
        
        from PySide6.QtWidgets import QSizePolicy
        self.bookings_table = QTableWidget(0, 10)
        self.bookings_table.setHorizontalHeaderLabels([
            "Booking #", "Date", "Customer", "Total Nights", "Room Type", "Pax", "Total Price", "Status", "Actions", "ID"
        ])
        
        # Stretch data columns, give Actions column a fixed comfortable width
        hdr = self.bookings_table.horizontalHeader()
        for col in range(8):  # Booking# through Status
            hdr.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)   # Actions
        self.bookings_table.setColumnWidth(8, 300)
        hdr.setSectionResizeMode(9, QHeaderView.ResizeMode.Fixed)   # Hidden ID
        self.bookings_table.setColumnHidden(9, True)
        
        self.bookings_table.setMinimumHeight(300)
        self.bookings_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.bookings_table.setAlternatingRowColors(True)
        self.bookings_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.bookings_table.verticalHeader().setVisible(False)
        self.bookings_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        # Removed: self.bookings_table.itemDoubleClicked.connect(self._edit_booking)
        bookings_layout.addWidget(self.bookings_table, 1)
        
        # Pagination for Bookings
        self.booking_pagination = PaginationWidget()
        self.booking_pagination.page_changed.connect(self._on_booking_page_changed)
        bookings_layout.addWidget(self.booking_pagination)
        
        self.tabs.addTab(bookings_tab, "Custom Bookings")

    def _on_template_page_changed(self, skip):
        self.current_template_skip = skip
        self.refresh_templates()

    def _on_booking_page_changed(self, skip):
        self.current_booking_skip = skip
        self.refresh_bookings()

    def refresh(self):
        self.current_template_skip = 0
        self.current_booking_skip = 0
        self.refresh_templates()
        self.refresh_bookings()
        
    def refresh_templates(self):
        self.template_cache.clear()
        self.pricing_cache.clear()
        query = self.search_input.text()
        self.viewmodel.load_templates(query=query, skip=self.current_template_skip, limit=self.limit)
        
    def refresh_bookings(self):
        query = self.search_input.text()
        self.viewmodel.load_bookings(query=query, skip=self.current_booking_skip, limit=self.limit)

    def _create_template(self):
        dialog = TemplateBuilderDialog(self.current_user.id, self)
        if dialog.exec():
            self.refresh()

    def _edit_template(self, template, pricing_list):
        dialog = TemplateBuilderDialog(self.current_user.id, self)
        dialog.load_template(template, pricing_list)
        if dialog.exec():
            self.refresh()

    def _delete_template(self, template):
        reply = QMessageBox.question(self, "Confirm Delete", 
            f"Are you sure you want to delete the template '{template.name}'?\nThis action cannot be undone.", 
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.viewmodel.delete_template(template.id, self.current_user.id)

    def _add_booking(self):
        dialog = UnifiedBookingWizardUI(parent=self)
        if dialog.exec():
            self.refresh()
            
    def _edit_booking(self, item):
        row = item.row()
        booking_id = self.bookings_table.item(row, 9).text()
        dialog = UnifiedBookingWizardUI(parent=self)
        dialog.load_booking(booking_id)
        if dialog.exec():
            self.refresh()

    def _on_templates_loaded(self, result):
        self.template_cache = result.get('items', [])
        total = result.get('total', 0)
        self.template_pagination.update_pagination(total, self.current_template_skip, self.limit)
        self.pending_pricing_requests = len(self.template_cache)
        
        if self.pending_pricing_requests == 0:
            self._render_cards()
        else:
            for t in self.template_cache:
                self.viewmodel.load_template_pricing(t.id)

    def _on_pricing_fetched_for_card(self, pricing_list):
        if pricing_list:
            t_id = pricing_list[0].template_id
            self.pricing_cache[t_id] = pricing_list
            
        self.pending_pricing_requests -= 1
        if self.pending_pricing_requests <= 0:
            self._render_cards()

    def _render_cards(self):
        # Clear existing cards safely
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        row, col = 0, 0
        max_cols = 2 # 2 cards per row
        
        for t in self.template_cache:
            p_list = self.pricing_cache.get(t.id, [])
            card = TemplateCard(t, p_list, self)
            self.cards_layout.addWidget(card, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def _on_bookings_loaded(self, result):
        items = result.get('items', [])
        total = result.get('total', 0)
        self.booking_pagination.update_pagination(total, self.current_booking_skip, self.limit)
        
        self.bookings_table.setRowCount(0)
        for b in items:
            row = self.bookings_table.rowCount()
            self.bookings_table.insertRow(row)
            self.bookings_table.setItem(row, 0, QTableWidgetItem(b.booking_number))
            
            date_str = b.created_at.strftime("%d-%b-%Y") if b.created_at else ""
            self.bookings_table.setItem(row, 1, QTableWidgetItem(date_str))
            
            self.bookings_table.setItem(row, 2, QTableWidgetItem(b.customer.full_name if b.customer else ""))
            self.bookings_table.setItem(row, 3, QTableWidgetItem(str(b.total_nights)))
            self.bookings_table.setItem(row, 4, QTableWidgetItem(b.room_type or ""))
            self.bookings_table.setItem(row, 5, QTableWidgetItem(str(b.total_pilgrims)))
            self.bookings_table.setItem(row, 6, QTableWidgetItem(f"{b.final_total_price:,.2f}"))
            self.bookings_table.setItem(row, 7, QTableWidgetItem(b.status))
            
            self.bookings_table.setRowHeight(row, 58)
            
            # Action Buttons Layout
            action_widget = QWidget()
            action_widget.setStyleSheet("background: transparent;")
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(6, 8, 6, 8)
            action_layout.setSpacing(6)
            
            btn_check = QPushButton("Check Services")
            btn_check.setFixedHeight(36)
            btn_check.setMinimumWidth(110)
            btn_check.setStyleSheet(
                "QPushButton { background: #2D3748; color: #E2E8F0; border: 1px solid rgba(255,255,255,0.12);"
                " border-radius: 6px; font-weight: 600; font-size: 9pt; padding: 0 8px; }"
                "QPushButton:hover { background: #4A5568; border: 1px solid #DD2476; color: #FFFFFF; }"
            )
            btn_check.clicked.connect(lambda checked, bid=str(b.id): self._open_check_services(bid))
            
            btn_print = QPushButton("Print Invoice  ▼")
            btn_print.setFixedHeight(36)
            btn_print.setMinimumWidth(115)
            btn_print.setStyleSheet(
                "QPushButton { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF512F, stop:1 #DD2476);"
                " color: white; border: none; border-radius: 6px; font-weight: bold; font-size: 9pt; padding: 0 8px; }"
                "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF6B4A, stop:1 #E83E8C); }"
                "QPushButton::menu-indicator { image: none; }"
            )
            print_menu = QMenu(btn_print)
            print_menu.setStyleSheet(
                "QMenu { background-color: #1C1C2D; border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; }"
                "QMenu::item { padding: 8px 20px; color: #E2E8F0; font-size: 10pt; }"
                "QMenu::item:selected { background-color: rgba(221,36,118,0.3); color: white; }"
            )
            
            act_master = QAction("Master Package Invoice", print_menu)
            act_master.triggered.connect(lambda checked, bid=str(b.id): self._print_invoice_from_row(bid, True))
            
            act_itemized = QAction("Itemized Breakdown Invoice", print_menu)
            act_itemized.triggered.connect(lambda checked, bid=str(b.id): self._print_invoice_from_row(bid, False))
            
            print_menu.addAction(act_master)
            print_menu.addAction(act_itemized)
            btn_print.setMenu(print_menu)
            
            action_layout.addWidget(btn_check)
            action_layout.addWidget(btn_print)
            action_layout.addStretch()
            
            self.bookings_table.setCellWidget(row, 8, action_widget)
            self.bookings_table.setItem(row, 9, QTableWidgetItem(str(b.id)))

    def _open_check_services(self, booking_id):
        dialog = CheckServicesDialog(booking_id, self, list_page=self)
        dialog.exec()
        self.refresh()   # always refresh in case user edited

    def _print_invoice_from_row(self, booking_id, is_summary):
        try:
            with get_session() as session:
                umrah = session.get(CustomUmrahBooking, booking_id)
                invoice = session.query(Invoice).filter_by(reference_id=umrah.id).first()
                if not invoice:
                    QMessageBox.warning(self, "No Invoice", "No invoice found for this booking.")
                    return
                
                pkg_name = umrah.template.name if umrah.template else "Custom Umrah"
                os.makedirs("invoices", exist_ok=True)
                suffix = "Master" if is_summary else "Itemized"
                path = os.path.abspath(f"invoices/Invoice_{invoice.invoice_number}_{suffix}.pdf")
                
                if is_summary:
                    InvoiceGenerator.generate_invoice_pdf(invoice, path, is_package_summary=True, package_name=pkg_name)
                else:
                    InvoiceGenerator.generate_umrah_group_invoice_pdf(invoice, path, umrah_booking=umrah)
                
                if os.path.exists(path):
                    os.startfile(path)
        except Exception as e:
            QMessageBox.critical(self, "Print Error", str(e))

    def _on_error(self, message):
        pass # Ignore minor pricing fetch errors, let cards render empty
