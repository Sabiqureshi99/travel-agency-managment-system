from PySide6.QtCore import QObject, Signal, QThread, QRunnable, QThreadPool
import traceback
from config.database import get_session
from models.transport import Vehicle, Driver, TransportBooking
from models.customer import Customer
from models.user import ActivityLog
from models.booking import Booking
from core.signals import app_signals
from datetime import datetime

class LoadVehiclesWorker(QRunnable):
    def __init__(self, signals, skip=0, limit=100):
        super().__init__()
        self.signals = signals
        self.skip = skip
        self.limit = limit
        
    def run(self):
        try:
            with get_session() as session:
                query = session.query(Vehicle)
                total = query.count()
                vehicles = query.order_by(Vehicle.created_at.desc()).offset(self.skip).limit(self.limit).all()
                
                # Detach objects for use in UI thread
                for v in vehicles:
                    session.expunge(v)
                    
                self.signals.result.emit({'vehicles': vehicles, 'total': total})
        except Exception as e:
            self.signals.error.emit(f"Failed to load vehicles: {str(e)}")

class LoadDriversWorker(QRunnable):
    def __init__(self, signals, skip=0, limit=100):
        super().__init__()
        self.signals = signals
        self.skip = skip
        self.limit = limit
        
    def run(self):
        try:
            with get_session() as session:
                query = session.query(Driver)
                total = query.count()
                drivers = query.order_by(Driver.created_at.desc()).offset(self.skip).limit(self.limit).all()
                
                for d in drivers:
                    session.expunge(d)
                    
                self.signals.result.emit({'drivers': drivers, 'total': total})
        except Exception as e:
            self.signals.error.emit(f"Failed to load drivers: {str(e)}")

class LoadBookingsWorker(QRunnable):
    def __init__(self, signals, skip=0, limit=100):
        super().__init__()
        self.signals = signals
        self.skip = skip
        self.limit = limit
        
    def run(self):
        try:
            with get_session() as session:
                query = session.query(TransportBooking)
                total = query.count()
                bookings = query.order_by(TransportBooking.created_at.desc()).offset(self.skip).limit(self.limit).all()
                
                for b in bookings:
                    if b.customer: pass
                    if b.vehicle: pass
                    if b.driver: pass
                    session.expunge(b)
                    
                self.signals.result.emit({'bookings': bookings, 'total': total})
        except Exception as e:
            self.signals.error.emit(f"Failed to load bookings: {str(e)}")

class LoadFormDataWorker(QRunnable):
    def __init__(self, signals):
        super().__init__()
        self.signals = signals
        
    def run(self):
        try:
            with get_session() as session:
                customers = session.query(Customer).filter_by(is_active=True).all()
                vehicles = session.query(Vehicle).filter_by(status='Available').all()
                drivers = session.query(Driver).filter_by(status='Available').all()
                
                for c in customers: session.expunge(c)
                for v in vehicles: session.expunge(v)
                for d in drivers: session.expunge(d)
                
                self.signals.result.emit({
                    'customers': customers,
                    'vehicles': vehicles,
                    'drivers': drivers
                })
        except Exception as e:
            self.signals.error.emit(f"Failed to load form data: {str(e)}")

class SaveVehicleWorker(QRunnable):
    def __init__(self, data, user_id, signals):
        super().__init__()
        self.data = data
        self.user_id = user_id
        self.signals = signals
        
    def run(self):
        try:
            with get_session() as session:
                if self.data.get('id'):
                    vehicle = session.query(Vehicle).get(self.data['id'])
                    is_new = False
                else:
                    vehicle = Vehicle()
                    is_new = True
                    
                for key, value in self.data.items():
                    if key != 'id':
                        setattr(vehicle, key, value)
                        
                if is_new:
                    session.add(vehicle)
                    
                # Log
                log = ActivityLog(
                    user_id=self.user_id,
                    action="CREATE_VEHICLE" if is_new else "UPDATE_VEHICLE",
                    module="Transport",
                    description=f"{'Created' if is_new else 'Updated'} Vehicle: {vehicle.registration_number}"
                )
                session.add(log)
                session.commit()
                
                session.refresh(vehicle)
                session.expunge(vehicle)
                self.signals.result.emit({'vehicle': vehicle})
        except Exception as e:
            self.signals.error.emit(f"Failed to save vehicle: {str(e)}\n{traceback.format_exc()}")

class SaveDriverWorker(QRunnable):
    def __init__(self, data, user_id, signals):
        super().__init__()
        self.data = data
        self.user_id = user_id
        self.signals = signals
        
    def run(self):
        try:
            with get_session() as session:
                if self.data.get('id'):
                    driver = session.query(Driver).get(self.data['id'])
                    is_new = False
                else:
                    driver = Driver()
                    is_new = True
                    
                for key, value in self.data.items():
                    if key != 'id':
                        setattr(driver, key, value)
                        
                if is_new:
                    session.add(driver)
                    
                log = ActivityLog(
                    user_id=self.user_id,
                    action="CREATE_DRIVER" if is_new else "UPDATE_DRIVER",
                    module="Transport",
                    description=f"{'Created' if is_new else 'Updated'} Driver: {driver.full_name}"
                )
                session.add(log)
                session.commit()
                
                session.refresh(driver)
                session.expunge(driver)
                self.signals.result.emit({'driver': driver})
        except Exception as e:
            self.signals.error.emit(f"Failed to save driver: {str(e)}\n{traceback.format_exc()}")

class SaveBookingWorker(QRunnable):
    def __init__(self, data, user_id, signals):
        super().__init__()
        self.data = data
        self.user_id = user_id
        self.signals = signals
        
    def run(self):
        try:
            with get_session() as session:
                if self.data.get('id'):
                    booking = session.query(TransportBooking).get(self.data['id'])
                    is_new = False
                else:
                    booking = TransportBooking()
                    # Generate booking number
                    today = datetime.now().strftime("%y%m%d")
                    count = session.query(TransportBooking).filter(
                        TransportBooking.booking_date >= datetime.now().date()
                    ).count() + 1
                    booking.booking_number = f"TRB-{today}-{count:03d}"
                    is_new = True
                    
                for key, value in self.data.items():
                    if key != 'id':
                        setattr(booking, key, value)
                        
                if is_new:
                    session.add(booking)
                    
                log = ActivityLog(
                    user_id=self.user_id,
                    action="CREATE_TRANSPORT_BKG" if is_new else "UPDATE_TRANSPORT_BKG",
                    module="Transport",
                    description=f"{'Created' if is_new else 'Updated'} Booking: {booking.booking_number}"
                )
                session.add(log)
                
                # Centralized Booking Record for reporting
                if is_new:
                    b_record = Booking(
                        booking_type='Transport_Only',
                        customer_id=booking.customer_id,
                        cost_price=booking.purchase_price if hasattr(booking, 'purchase_price') else 0.0,
                        selling_price=booking.sales_price if hasattr(booking, 'sales_price') else 0.0
                    )
                    session.add(b_record)
                    
                session.commit()
                
                # Emit global signal for list refreshes
                try:
                    app_signals.transport_added.emit()
                except Exception:
                    pass
                
                session.refresh(booking)
                session.expunge(booking)
                self.signals.result.emit({'booking': booking})
        except Exception as e:
            self.signals.error.emit(f"Failed to save booking: {str(e)}\n{traceback.format_exc()}")


class TransportSignals(QObject):
    vehicles_loaded = Signal(dict)
    drivers_loaded = Signal(dict)
    bookings_loaded = Signal(dict)
    vehicle_saved = Signal(dict)
    driver_saved = Signal(dict)
    booking_saved = Signal(dict)
    form_data_loaded = Signal(dict)
    error = Signal(str)

class TransportViewModel(QObject):
    vehicles_loaded = Signal(dict)
    drivers_loaded = Signal(dict)
    bookings_loaded = Signal(dict)
    vehicle_saved = Signal(dict)
    driver_saved = Signal(dict)
    booking_saved = Signal(dict)
    form_data_loaded = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self):
        super().__init__()
        self.thread_pool = QThreadPool.globalInstance()

    def load_vehicles(self, skip=0, limit=100):
        signals = TransportSignals()
        signals.result = self.vehicles_loaded
        signals.error.connect(self.error_occurred)
        worker = LoadVehiclesWorker(signals, skip, limit)
        self.thread_pool.start(worker)

    def load_drivers(self, skip=0, limit=100):
        signals = TransportSignals()
        signals.result = self.drivers_loaded
        signals.error.connect(self.error_occurred)
        worker = LoadDriversWorker(signals, skip, limit)
        self.thread_pool.start(worker)

    def load_bookings(self, skip=0, limit=100):
        signals = TransportSignals()
        signals.result = self.bookings_loaded
        signals.error.connect(self.error_occurred)
        worker = LoadBookingsWorker(signals, skip, limit)
        self.thread_pool.start(worker)
        
    def load_form_data(self):
        signals = TransportSignals()
        signals.result = self.form_data_loaded
        signals.error.connect(self.error_occurred)
        worker = LoadFormDataWorker(signals)
        self.thread_pool.start(worker)

    def save_vehicle(self, data, user_id):
        signals = TransportSignals()
        signals.result = self.vehicle_saved
        signals.error.connect(self.error_occurred)
        worker = SaveVehicleWorker(data, user_id, signals)
        self.thread_pool.start(worker)

    def save_driver(self, data, user_id):
        signals = TransportSignals()
        signals.result = self.driver_saved
        signals.error.connect(self.error_occurred)
        worker = SaveDriverWorker(data, user_id, signals)
        self.thread_pool.start(worker)
        
    def save_booking(self, data, user_id):
        signals = TransportSignals()
        signals.result = self.booking_saved
        signals.error.connect(self.error_occurred)
        worker = SaveBookingWorker(data, user_id, signals)
        self.thread_pool.start(worker)
