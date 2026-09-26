from typing import Optional, List
from datetime import date
from sqlalchemy import String, Boolean, Integer, Date, Text, Numeric, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.base_model import BaseModel

class UmrahPackageTemplate(BaseModel):
    __tablename__ = 'umrah_package_templates'

    name: Mapped[str] = mapped_column(String(300), nullable=False)
    star_rating: Mapped[float] = mapped_column(Numeric(3, 1), default=3.0)
    currency: Mapped[str] = mapped_column(String(10), default='PKR')
    
    total_nights: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    makkah_hotel: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    makkah_nights: Mapped[int] = mapped_column(Integer, default=0)
    
    medinah_hotel: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    medinah_nights: Mapped[int] = mapped_column(Integer, default=0)
    
    meal_plan: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    inclusions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    status: Mapped[str] = mapped_column(String(20), default='Active')

    pricing: Mapped[List["UmrahPackagePricing"]] = relationship(back_populates="template", cascade="all, delete-orphan")
    bookings: Mapped[List["CustomUmrahBooking"]] = relationship(back_populates="template")

    def __repr__(self) -> str:
        return f"<UmrahPackageTemplate {self.name}>"


class UmrahPackagePricing(BaseModel):
    __tablename__ = 'umrah_package_pricing'

    template_id: Mapped[str] = mapped_column(String(36), ForeignKey('umrah_package_templates.id'), index=True, nullable=False)
    room_type: Mapped[str] = mapped_column(String(50), nullable=False)  # Double, Triple, Quad
    price_per_person: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    template: Mapped["UmrahPackageTemplate"] = relationship(back_populates="pricing")

    def __repr__(self) -> str:
        return f"<UmrahPackagePricing {self.room_type} {self.price_per_person}>"


class CustomUmrahBooking(BaseModel):
    __tablename__ = 'custom_umrah_bookings'

    booking_number: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey('customers.id'), index=True, nullable=False)
    template_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey('umrah_package_templates.id'), nullable=True)
    
    booking_date: Mapped[date] = mapped_column(Date, nullable=False)
    departure_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    room_type: Mapped[str] = mapped_column(String(50), nullable=True)
    total_nights: Mapped[int] = mapped_column(Integer, default=0)
    total_pilgrims: Mapped[int] = mapped_column(Integer, default=1)
    
    base_package_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    base_purchase_cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    base_profit: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    airfare_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    final_total_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    amount_paid: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    
    flight_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    visa_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    hotel_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    transport_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ziyarat_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    supplements: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default='Pending')
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="umrah_bookings")
    template: Mapped[Optional["UmrahPackageTemplate"]] = relationship("UmrahPackageTemplate")
    pilgrims: Mapped[List["UmrahPilgrim"]] = relationship(back_populates="booking", cascade="all, delete-orphan")
    
    # Cross-Module Links
    flights: Mapped[List["FlightBooking"]] = relationship("FlightBooking", back_populates="umrah_booking", cascade="all, delete-orphan")
    visas: Mapped[List["VisaApplication"]] = relationship("VisaApplication", back_populates="umrah_booking", cascade="all, delete-orphan")
    hotels: Mapped[List["HotelBooking"]] = relationship("HotelBooking", back_populates="umrah_booking", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<CustomUmrahBooking {self.booking_number}>"


class UmrahPilgrim(BaseModel):
    __tablename__ = 'umrah_pilgrims'

    booking_id: Mapped[str] = mapped_column(String(36), ForeignKey('custom_umrah_bookings.id'), index=True, nullable=False)
    pax_type: Mapped[str] = mapped_column(String(10), nullable=False, default="Adult")
    title: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    passport_number: Mapped[str] = mapped_column(String(50), nullable=False)
    passport_expiry: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    group_no: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    relation: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    visa_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    ticket_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    room_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    departure_flight: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    return_flight: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    booking: Mapped["CustomUmrahBooking"] = relationship(back_populates="pilgrims")

    def __repr__(self) -> str:
        return f"<UmrahPilgrim {self.full_name}>"
