from typing import Optional, List
from datetime import date
from sqlalchemy import String, Boolean, Date, Text, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.base_model import BaseModel

class FlightSegment(BaseModel):
    __tablename__ = 'flight_segments'
    
    booking_id: Mapped[str] = mapped_column(String(36), ForeignKey('flight_bookings.id'), index=True, nullable=False)
    origin: Mapped[str] = mapped_column(String(200), nullable=False)
    destination: Mapped[str] = mapped_column(String(200), nullable=False)
    departure_date: Mapped[date] = mapped_column(Date, nullable=False)
    departure_time: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    airline: Mapped[str] = mapped_column(String(200), nullable=False)
    flight_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    cabin_class: Mapped[str] = mapped_column(String(30), default='Economy')
    
    booking: Mapped["FlightBooking"] = relationship(back_populates="segments")

class FlightBooking(BaseModel):
    __tablename__ = 'flight_bookings'

    booking_number: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey('customers.id'), index=True, nullable=False)
    vendor_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey('vendors.id'), nullable=True)
    umrah_booking_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey('custom_umrah_bookings.id'), index=True, nullable=True)
    flight_type: Mapped[str] = mapped_column(String(20), nullable=False)
    trip_type: Mapped[str] = mapped_column(String(20), nullable=False)
    leg_type: Mapped[str] = mapped_column(String(30), default='Outbound')
    airline: Mapped[str] = mapped_column(String(200), nullable=False)
    flight_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    origin: Mapped[str] = mapped_column(String(200), nullable=False)
    destination: Mapped[str] = mapped_column(String(200), nullable=False)
    departure_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    departure_time: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    arrival_time: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    arrival_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    return_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    return_airline: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    cabin_class: Mapped[str] = mapped_column(String(30), default='Economy')
    pnr: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    booking_status: Mapped[str] = mapped_column(String(30), default='Confirmed')
    base_fare: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    taxes: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    vendor_fare: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    selling_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    commission: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    purchase_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    sales_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    profit: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    currency: Mapped[str] = mapped_column(String(10), default='PKR')
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="flight_bookings")
    vendor: Mapped[Optional["Vendor"]] = relationship("Vendor", back_populates="flight_bookings")
    umrah_booking: Mapped[Optional["CustomUmrahBooking"]] = relationship("CustomUmrahBooking", back_populates="flights")
    passengers: Mapped[List["FlightPassenger"]] = relationship(back_populates="booking", cascade="all, delete-orphan")
    segments: Mapped[List["FlightSegment"]] = relationship(back_populates="booking", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<FlightBooking {self.booking_number}>"


class FlightPassenger(BaseModel):
    __tablename__ = 'flight_passengers'

    booking_id: Mapped[str] = mapped_column(String(36), ForeignKey('flight_bookings.id'), index=True, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    passport_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    passport_expiry: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    nationality: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, default='Pakistani')
    ticket_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    ticket_status: Mapped[str] = mapped_column(String(30), default='Issued')
    seat_number: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    booking: Mapped["FlightBooking"] = relationship(back_populates="passengers")

    def __repr__(self) -> str:
        return f"<FlightPassenger {self.first_name} {self.last_name}>"
