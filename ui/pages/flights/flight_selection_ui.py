"""
FlightCard & FlightSelectionView
Pixel-perfect recreation of the OTA flight listing UI shown in the reference image.

Layout (per card):
  [Logo + Airline + Flight# + Cabin] | [DepTime  ──duration──  ArrTime]
                                      | [Route row: KHI - Nonstop - JED]
                                      | [Amenity icons]
  ────────────────────────────────── | ─────────────────────────────────
  (vertical separator)               | [Save badge?]  [PKR button]
"""
from typing import Dict, Any, List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QSizePolicy, QSpacerItem, QApplication
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QRect, QSize
from PySide6.QtGui import QFont, QPixmap, QColor, QPainter, QPainterPath, QLinearGradient, QBrush


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _label(text: str, pt: int = 10, bold: bool = False, color: str = None) -> QLabel:
    lbl = QLabel(text)
    f = QFont("Segoe UI", pt)
    f.setBold(bold)
    lbl.setFont(f)
    if color:
        lbl.setStyleSheet(f"color: {color}; background: transparent; border: none;")
    else:
        lbl.setStyleSheet("background: transparent; border: none;")
    return lbl


def _airline_initial_badge(text: str, color: str = "#1E3A5F") -> QLabel:
    """Circular badge showing first 2 letters of airline."""
    lbl = QLabel(text[:2].upper())
    lbl.setFixedSize(48, 48)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setStyleSheet(f"""
        QLabel {{
            background: {color};
            color: white;
            border-radius: 24px;
            font-size: 15px;
            font-weight: bold;
            border: none;
        }}
    """)
    return lbl


# Airline → brand color mapping
AIRLINE_COLORS = {
    "airsial":    "#006B3F",
    "airblue":    "#004A97",
    "pia":        "#006A4E",
    "fly jinnah": "#E31837",
    "flydubai":   "#E31837",
    "qatar airways": "#5C0632",
    "emirates":   "#D4A017",
    "lufthansa":  "#05164D",
    "turkish airlines": "#C8102E",
    "air arabia": "#EF3340",
}


def _get_airline_color(name: str) -> str:
    return AIRLINE_COLORS.get(name.lower().strip(), "#334155")


# ---------------------------------------------------------------------------
# FlightCard
# ---------------------------------------------------------------------------

class FlightCard(QFrame):
    """
    Single flight option card matching the OTA reference design.

    Card structure:
    ┌──────────────────────────────────────────────────────────────┐
    │  [Logo]   DEP_TIME  [duration pill]  ARR_TIME  │  [Price btn] │
    │  Airline  Origin  ─ Nonstop ─ Dest             │              │
    │  FltNum   🧳 Baggage  🍽 Meal                   │  [Save badge]│
    └──────────────────────────────────────────────────────────────┘
    """
    flight_selected = Signal(dict)

    def __init__(self, flight_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.flight_data = flight_data
        self._selected = False
        self._setup_card()

    def _setup_card(self):
        self.setObjectName("FlightCard")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(110)
        self._apply_style(selected=False)

        root = QHBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(0)

        # ── LEFT: Airline identity ──────────────────────────────────
        airline_name = self.flight_data.get("airline_name", "Unknown")
        flight_no    = self.flight_data.get("flight_number", "")
        cabin        = self.flight_data.get("cabin_class", "")

        left = QVBoxLayout()
        left.setSpacing(2)
        left.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        logo_path = self.flight_data.get("logo_path", "")
        pixmap = QPixmap(logo_path) if logo_path else QPixmap()
        if not pixmap.isNull():
            logo_lbl = QLabel()
            logo_lbl.setPixmap(pixmap.scaledToHeight(36, Qt.TransformationMode.SmoothTransformation))
            logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            left.addWidget(logo_lbl)
        else:
            badge = _airline_initial_badge(airline_name, _get_airline_color(airline_name))
            left.addWidget(badge, alignment=Qt.AlignmentFlag.AlignHCenter)

        left.addWidget(_label(airline_name, 9, True), alignment=Qt.AlignmentFlag.AlignHCenter)
        left.addWidget(_label(flight_no, 8, False), alignment=Qt.AlignmentFlag.AlignHCenter)
        if cabin:
            left.addWidget(_label(f"({cabin})", 7, False), alignment=Qt.AlignmentFlag.AlignHCenter)

        left_widget = QWidget()
        left_widget.setLayout(left)
        left_widget.setFixedWidth(110)

        root.addWidget(left_widget)

        # ── DIVIDER ─────────────────────────────────────────────────
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.VLine)
        sep1.setStyleSheet("border: none; border-left: 1px solid #E2E8F0;")
        sep1.setFixedWidth(1)
        root.addWidget(sep1)
        root.addSpacing(20)

        # ── MIDDLE: Route timeline ───────────────────────────────────
        dep_time  = self.flight_data.get("departure_time", "--:--")
        arr_time  = self.flight_data.get("arrival_time", "--:--")
        dep_ap    = self.flight_data.get("departure_airport", "")
        arr_ap    = self.flight_data.get("arrival_airport", "")
        origin    = self.flight_data.get("origin", "")
        dest      = self.flight_data.get("destination", "")
        duration  = self.flight_data.get("duration", "")
        stops     = self.flight_data.get("stops", "Nonstop")
        baggage   = self.flight_data.get("baggage", "")
        meal      = self.flight_data.get("meal", "")

        dep_loc = f"{origin} ({dep_ap})" if dep_ap else origin
        arr_loc = f"{dest} ({arr_ap})" if arr_ap else dest

        mid = QVBoxLayout()
        mid.setSpacing(4)
        mid.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # ---- Row 1: Times + duration pill ----
        time_row = QHBoxLayout()
        time_row.setSpacing(10)
        time_row.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Departure time (big)
        dep_lbl = _label(dep_time, 18, True)
        time_row.addWidget(dep_lbl)

        # Duration pill
        if duration:
            dur_pill = QLabel(duration)
            dur_pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
            dur_pill.setStyleSheet("""
                QLabel {
                    border-radius: 10px;
                    padding: 2px 10px;
                    font-size: 9pt;
                    border: 1px solid #475569;
                }
            """)
            dur_pill.setFixedHeight(22)
            time_row.addWidget(dur_pill)

        # Arrival time (big)
        arr_lbl = _label(arr_time, 18, True)
        time_row.addWidget(arr_lbl)

        time_row.addStretch()
        mid.addLayout(time_row)

        # ---- Row 2: Route text (KHI - Nonstop - JED) ----
        stops_color = "#16A34A" if "nonstop" in stops.lower() or "direct" in stops.lower() or "0" in stops else "#DC2626"
        route_text = f"{dep_loc}  ─  {stops}  ─  {arr_loc}"
        route_lbl = _label(route_text, 9, False)
        mid.addWidget(route_lbl)

        # ---- Row 3: Amenities ----
        amenity_row = QHBoxLayout()
        amenity_row.setSpacing(14)
        amenity_row.setAlignment(Qt.AlignmentFlag.AlignLeft)

        if baggage:
            bag_lbl = _label(f"🧳 {baggage}", 8, False)
            amenity_row.addWidget(bag_lbl)
        if meal:
            meal_lbl = _label(f"🍽 {meal}", 8, False)
            amenity_row.addWidget(meal_lbl)
        amenity_row.addStretch()
        mid.addLayout(amenity_row)

        mid_widget = QWidget()
        mid_widget.setLayout(mid)
        root.addWidget(mid_widget, stretch=1)

        # ── DIVIDER ─────────────────────────────────────────────────
        root.addSpacing(20)
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.VLine)
        sep2.setStyleSheet("border: none; border-left: 1px solid #E2E8F0;")
        sep2.setFixedWidth(1)
        root.addWidget(sep2)
        root.addSpacing(20)

        # ── RIGHT: Price + CTA ───────────────────────────────────────
        price      = self.flight_data.get("total_price", 0.0)
        savings    = self.flight_data.get("savings", 0)

        right = QVBoxLayout()
        right.setSpacing(8)
        right.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        # "Save PKR XX,XXX" badge (optional)
        if savings and float(savings) > 0:
            save_lbl = QLabel(f"Save PKR {float(savings):,.0f} ⓘ")
            save_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            save_lbl.setStyleSheet("""
                QLabel {
                    background: transparent;
                    color: #16A34A;
                    border: 1px solid #16A34A;
                    border-radius: 4px;
                    padding: 2px 8px;
                    font-size: 8.5pt;
                }
            """)
            right.addWidget(save_lbl, alignment=Qt.AlignmentFlag.AlignRight)

        # Price button (big, dark blue)
        price_btn = QPushButton(f"PKR {float(price):,.0f}")
        price_btn.setFixedWidth(160)
        price_btn.setFixedHeight(44)
        price_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        price_btn.setStyleSheet("""
            QPushButton {
                background: #1E3A5F;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14pt;
                font-weight: bold;
                letter-spacing: 0.3px;
            }
            QPushButton:hover {
                background: #1E40AF;
            }
            QPushButton:pressed {
                background: #1E3A8A;
            }
        """)
        price_btn.clicked.connect(self._on_select)
        right.addWidget(price_btn, alignment=Qt.AlignmentFlag.AlignRight)

        right_widget = QWidget()
        right_widget.setLayout(right)
        right_widget.setFixedWidth(185)
        root.addWidget(right_widget)

    def _apply_style(self, selected: bool):
        if selected:
            self.setStyleSheet("""
                QFrame#FlightCard {
                    background: #2D142C;
                    border-radius: 12px;
                    border: 2px solid #D81B60;
                }
                QWidget { background: transparent; border: none; }
            """)
        else:
            self.setStyleSheet("""
                QFrame#FlightCard {
                    background: #232332;
                    border-radius: 12px;
                    border: 1px solid #3F3F5A;
                }
                QFrame#FlightCard:hover {
                    border: 1px solid #D81B60;
                    background: #2A2A3D;
                }
                QWidget { background: transparent; border: none; }
            """)

    def _on_select(self):
        self._selected = True
        self._apply_style(selected=True)
        self.flight_selected.emit(self.flight_data)

    def deselect(self):
        self._selected = False
        self._apply_style(selected=False)


# ---------------------------------------------------------------------------
# FlightSelectionView
# ---------------------------------------------------------------------------

class FlightSelectionView(QWidget):
    """
    Scrollable OTA-style flight selection panel.
    Emits flight_selected(dict) when user clicks a price button.
    """
    flight_selected = Signal(dict)

    # Track all cards so we can deselect others on new selection
    _all_cards: List[FlightCard]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_cards = []
        self._init_ui()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Filter/sort bar ──────────────────────────────────────
        filter_bar = QWidget()
        filter_bar.setStyleSheet("background: #232332; border-bottom: 1px solid #3F3F5A;")
        fb_layout = QHBoxLayout(filter_bar)
        fb_layout.setContentsMargins(16, 8, 16, 8)

        avail_lbl = _label("Available Flights", 11, True)
        fb_layout.addWidget(avail_lbl)
        fb_layout.addStretch()

        sort_lbl = _label("Sort: Price ↑", 9, False)
        fb_layout.addWidget(sort_lbl)

        root.addWidget(filter_bar)

        # ── Scroll area ──────────────────────────────────────────
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setStyleSheet("background: transparent;")
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")

        self.cards_layout = QVBoxLayout(self.container)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.cards_layout.setSpacing(10)
        self.cards_layout.setContentsMargins(16, 16, 16, 16)

        self.scroll.setWidget(self.container)
        root.addWidget(self.scroll)

    def load_flights(self, flights_data: List[Dict[str, Any]]):
        """Clear and reload all flight cards from data list."""
        # Clear
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._all_cards.clear()

        if not flights_data:
            no_lbl = _label("No flights found for this route.", 11, False, "#64748B")
            no_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.cards_layout.addWidget(no_lbl)
            return

        for data in flights_data:
            card = FlightCard(data)
            card.flight_selected.connect(self._on_card_selected)
            self.cards_layout.addWidget(card)
            self._all_cards.append(card)

    def _on_card_selected(self, flight_data: dict):
        # Visually deselect all other cards
        for card in self._all_cards:
            if card.flight_data is not flight_data:
                card.deselect()
        self.flight_selected.emit(flight_data)
