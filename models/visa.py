from typing import TYPE_CHECKING, Optional, List
from datetime import date
from sqlalchemy import String, Integer, Date, Text, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.base_model import BaseModel
if TYPE_CHECKING:
    from models.customer import Customer
    from models.vendor import Vendor
    from models.custom_umrah_booking import CustomUmrahBooking


class VisaApplication(BaseModel):
    __tablename__ = 'visa_applications'

    application_number: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey('customers.id'), index=True, nullable=False)
    vendor_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey('vendors.id'), nullable=True)
    umrah_booking_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey('custom_umrah_bookings.id'), index=True, nullable=True)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    visa_type: Mapped[str] = mapped_column(String(50), nullable=False)
    embassy: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    application_date: Mapped[date] = mapped_column(Date, nullable=False)
    appointment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    appointment_time: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    submission_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    decision_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    visa_validity_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    entries_allowed: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default='Applied')
    fees_charged: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    embassy_fees: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    service_charges: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    total_cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    purchase_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    sales_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    profit: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    currency: Mapped[str] = mapped_column(String(10), default='PKR')
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    vendor_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey('vendors.id'), nullable=True)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="visa_applications")
    vendor: Mapped[Optional["Vendor"]] = relationship("Vendor", back_populates="visa_applications")
    vendor: Mapped[Optional["Vendor"]] = relationship("Vendor", back_populates="visa_applications")
    umrah_booking: Mapped[Optional["CustomUmrahBooking"]] = relationship("CustomUmrahBooking", back_populates="visas")
    applicants: Mapped[List["VisaApplicant"]] = relationship(back_populates="visa_application", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<VisaApplication {self.application_number}>"


class VisaApplicant(BaseModel):
    __tablename__ = 'visa_applicants'

    visa_application_id: Mapped[str] = mapped_column(String(36), ForeignKey('visa_applications.id'), index=True, nullable=False)
    customer_family_member_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey('customer_family_members.id'), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    passport_number: Mapped[str] = mapped_column(String(50), nullable=False)
    passport_expiry: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    fees: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    visa_application: Mapped["VisaApplication"] = relationship(back_populates="applicants")

    def __repr__(self) -> str:
        return f"<VisaApplicant {self.full_name}>"
