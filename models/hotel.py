from typing import TYPE_CHECKING, Optional, List
from datetime import date
from sqlalchemy import String, Integer, Date, Text, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.base_model import BaseModel
if TYPE_CHECKING:
    from models.vendor import Vendor
    from models.customer import Customer
    from models.custom_umrah_booking import CustomUmrahBooking


class Hotel(BaseModel):
    __tablename__ = 'hotels'

    hotel_code: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    hotel_name: Mapped[str] = mapped_column(String(300), nullable=False)
    chain: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    star_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    vendor_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey('vendors.id'), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default='PKR')
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default='Active')

    vendor: Mapped[Optional["Vendor"]] = relationship("Vendor", back_populates="hotels")
    bookings: Mapped[List["HotelBooking"]] = relationship(back_populates="hotel", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Hotel {self.hotel_code}>"


class HotelBooking(BaseModel):
    __tablename__ = 'hotel_bookings'

    booking_number: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    hotel_id: Mapped[str] = mapped_column(String(36), ForeignKey('hotels.id'), nullable=False)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey('customers.id'), index=True, nullable=False)
    vendor_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey('vendors.id'), nullable=True)
    umrah_booking_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey('custom_umrah_bookings.id'), index=True, nullable=True)
    check_in_date: Mapped[date] = mapped_column(Date, nullable=False)
    check_out_date: Mapped[date] = mapped_column(Date, nullable=False)
    city: Mapped[str] = mapped_column(String(100), default='Unknown')
    hn_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    hotel_name_override: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    reservation_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    nights: Mapped[int] = mapped_column(Integer, default=1)
    room_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    num_rooms: Mapped[int] = mapped_column(Integer, default=1)
    num_guests: Mapped[int] = mapped_column(Integer, default=1)
    vendor_rate: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    selling_rate: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    total_cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    total_selling: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    commission: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    purchase_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    sales_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    profit: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    currency: Mapped[str] = mapped_column(String(10), default='PKR')
    status: Mapped[str] = mapped_column(String(30), default='Confirmed')
    special_requests: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    voucher_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    hotel: Mapped["Hotel"] = relationship(back_populates="bookings")
    customer: Mapped["Customer"] = relationship("Customer", back_populates="hotel_bookings")
    vendor: Mapped[Optional["Vendor"]] = relationship("Vendor", back_populates="hotel_bookings")
    umrah_booking: Mapped[Optional["CustomUmrahBooking"]] = relationship("CustomUmrahBooking", back_populates="hotels")

    def __repr__(self) -> str:
        return f"<HotelBooking {self.booking_number}>"
