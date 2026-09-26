from typing import TYPE_CHECKING, Optional, List
from datetime import date
from sqlalchemy import String, Integer, Date, Text, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.base_model import BaseModel
if TYPE_CHECKING:
    from models.employee import Employee
    from models.customer import Customer
    from models.vendor import Vendor


class Vehicle(BaseModel):
    __tablename__ = 'vehicles'

    registration_number: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    make: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    vehicle_type: Mapped[str] = mapped_column(String(50), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, default=4)
    color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    chassis_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    engine_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default='Available')
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    bookings: Mapped[List["TransportBooking"]] = relationship(back_populates="vehicle", cascade="all, delete-orphan")
    maintenance_logs: Mapped[List["MaintenanceLog"]] = relationship(back_populates="vehicle", cascade="all, delete-orphan")
    fuel_logs: Mapped[List["FuelLog"]] = relationship(back_populates="vehicle", cascade="all, delete-orphan")


class Driver(BaseModel):
    __tablename__ = 'drivers'

    employee_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey('employees.id'), nullable=True)
    license_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    license_type: Mapped[str] = mapped_column(String(30), nullable=False)
    license_expiry: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default='Available')
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    employee: Mapped[Optional["Employee"]] = relationship("Employee")
    bookings: Mapped[List["TransportBooking"]] = relationship(back_populates="driver", cascade="all, delete-orphan")


class TransportBooking(BaseModel):
    __tablename__ = 'transport_bookings'

    booking_number: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey('customers.id'), index=True, nullable=False)
    vehicle_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey('vehicles.id'), nullable=True)
    driver_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey('drivers.id'), nullable=True)
    booking_date: Mapped[date] = mapped_column(Date, nullable=False)
    pickup_location: Mapped[str] = mapped_column(String(300), nullable=False)
    dropoff_location: Mapped[str] = mapped_column(String(300), nullable=False)
    service_route: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    tn_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    vehicle_type_override: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    contact_person: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    booking_ref: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pickup_date: Mapped[date] = mapped_column(Date, nullable=False)
    pickup_time: Mapped[str] = mapped_column(String(10), nullable=False)
    return_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    purchase_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    sales_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    profit: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    status: Mapped[str] = mapped_column(String(30), default='Confirmed')
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    vendor_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey('vendors.id'), nullable=True)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="transport_bookings")
    vehicle: Mapped[Optional["Vehicle"]] = relationship(back_populates="bookings")
    driver: Mapped[Optional["Driver"]] = relationship(back_populates="bookings")
    vendor: Mapped[Optional["Vendor"]] = relationship("Vendor", back_populates="transport_bookings")


class MaintenanceLog(BaseModel):
    __tablename__ = 'maintenance_logs'

    vehicle_id: Mapped[str] = mapped_column(String(36), ForeignKey('vehicles.id'), index=True, nullable=False)
    maintenance_date: Mapped[date] = mapped_column(Date, nullable=False)
    service_type: Mapped[str] = mapped_column(String(100), nullable=False)
    cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    workshop_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    vehicle: Mapped["Vehicle"] = relationship(back_populates="maintenance_logs")


class FuelLog(BaseModel):
    __tablename__ = 'fuel_logs'

    vehicle_id: Mapped[str] = mapped_column(String(36), ForeignKey('vehicles.id'), index=True, nullable=False)
    date_filled: Mapped[date] = mapped_column(Date, nullable=False)
    liters: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    cost_per_liter: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    total_cost: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    odometer_reading: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    station_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    vehicle: Mapped["Vehicle"] = relationship(back_populates="fuel_logs")
