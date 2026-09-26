from typing import Optional, List
from datetime import date
from sqlalchemy import String, Integer, Date, Text, Numeric, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.base_model import BaseModel

class TourPackage(BaseModel):
    __tablename__ = 'tour_packages'

    package_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    package_name: Mapped[str] = mapped_column(String(300), nullable=False)
    package_type: Mapped[str] = mapped_column(String(30), default='Domestic')
    destination: Mapped[str] = mapped_column(String(200), nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, default=1)
    duration_nights: Mapped[int] = mapped_column(Integer, default=0)
    includes: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    itinerary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    base_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    currency: Mapped[str] = mapped_column(String(10), default='PKR')
    max_capacity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default='Active')
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    bookings: Mapped[List["TourBooking"]] = relationship(back_populates="package", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<TourPackage {self.package_code}>"


class TourBooking(BaseModel):
    __tablename__ = 'tour_bookings'

    booking_number: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    package_id: Mapped[str] = mapped_column(String(36), ForeignKey('tour_packages.id'), nullable=False)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey('customers.id'), index=True, nullable=False)
    booking_date: Mapped[date] = mapped_column(Date, nullable=False)
    travel_date: Mapped[date] = mapped_column(Date, nullable=False)
    return_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    num_adults: Mapped[int] = mapped_column(Integer, default=1)
    num_children: Mapped[int] = mapped_column(Integer, default=0)
    total_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    amount_paid: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    amount_remaining: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    status: Mapped[str] = mapped_column(String(30), default='Confirmed')
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    package: Mapped["TourPackage"] = relationship(back_populates="bookings")
    customer: Mapped["Customer"] = relationship("Customer", back_populates="tour_bookings")

    def __repr__(self) -> str:
        return f"<TourBooking {self.booking_number}>"
