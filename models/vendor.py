from typing import TYPE_CHECKING, Optional
import sqlalchemy
from sqlalchemy import String, Text, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.base_model import BaseModel
if TYPE_CHECKING:
    from models.flight_booking import FlightBooking
    from models.visa_application import VisaApplication
    from models.hotel import HotelBooking, Hotel
    from models.transport import TransportBooking
    from models.vendor_payment import VendorPayment


class Vendor(BaseModel):
    __tablename__ = 'vendors'

    vendor_code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    company_name: Mapped[str] = mapped_column(String(300), nullable=False)
    vendor_type: Mapped[str] = mapped_column(String(50), nullable=False)
    contact_person: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    makkah_contact: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    madinah_contact: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    makkah_helpline_phone: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    makkah_helpline_whatsapp: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    madinah_helpline_phone: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    madinah_helpline_whatsapp: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, default='Pakistan')
    ntn: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    bank_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    bank_account_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    opening_balance: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    credit_limit: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    currency: Mapped[str] = mapped_column(String(10), default='PKR')
    payment_terms: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default='Active')
    
    flight_bookings: Mapped[list["FlightBooking"]] = relationship("FlightBooking", back_populates="vendor")
    visa_applications: Mapped[list["VisaApplication"]] = relationship("VisaApplication", back_populates="vendor")
    hotel_bookings: Mapped[list["HotelBooking"]] = relationship("HotelBooking", back_populates="vendor")
    transport_bookings: Mapped[list["TransportBooking"]] = relationship("TransportBooking", back_populates="vendor")
    hotels: Mapped[list["Hotel"]] = relationship("Hotel", back_populates="vendor")
    vendor_payments: Mapped[list["VendorPayment"]] = relationship("VendorPayment", back_populates="vendor")

    def __repr__(self) -> str:
        return f"<Vendor {self.vendor_code} {self.company_name}>"


class VendorLedger(BaseModel):
    """Ledger table for tracking vendor transactions (COGS)."""
    __tablename__ = 'vendor_ledgers'

    vendor_id: Mapped[str] = mapped_column(String(36), sqlalchemy.ForeignKey('vendors.id'), index=True, nullable=False)
    transaction_date: Mapped[sqlalchemy.Date] = mapped_column(sqlalchemy.Date, default=sqlalchemy.func.current_date())
    debit: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    credit: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    reference_booking_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payment_source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # 'Cash Drawer' or 'Main Bank Account'

    vendor: Mapped["Vendor"] = relationship("Vendor")

