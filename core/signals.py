"""
core/signals.py
================
Global Event Bus for cross-module decoupling.
Enables independent UI tabs to listen for backend state changes (e.g., successful DB commits)
and refresh themselves without direct coupling.
"""

from PySide6.QtCore import QObject, Signal

class GlobalSignals(QObject):
    # Core Transactions
    umrah_checkout_completed = Signal()
    flight_added = Signal()
    hotel_added = Signal()
    visa_added = Signal()
    transport_added = Signal()
    
    # Financials
    invoice_generated = Signal()
    payment_processed = Signal()
    payment_received = Signal(str)
    
    # Customers
    customer_added = Signal()
    
    # General data change (passing module name)
    data_changed = Signal(str)
    
    # Settings
    company_profile_updated = Signal()

# Singleton instance exported for application-wide use
app_signals = GlobalSignals()
