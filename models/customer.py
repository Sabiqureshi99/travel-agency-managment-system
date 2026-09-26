from typing import Optional, List
from datetime import date
from sqlalchemy import String, Boolean, Date, Text, Numeric, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.base_model import BaseModel

class Customer(BaseModel):
    __tablename__ = 'customers'
    __table_args__ = (
        CheckConstraint('cnic IS NOT NULL OR passport_number IS NOT NULL', name='check_customer_id_provided'),
    )

    customer_code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    customer_type: Mapped[str] = mapped_column(String(20), default='Individual')
    title: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    father_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    nationality: Mapped[str] = mapped_column(String(100), default='Pakistani')
    cnic: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    passport_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    passport_issue_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    passport_expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    passport_issue_place: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    phone_primary: Mapped[str] = mapped_column(String(20), nullable=False)
    phone_whatsapp: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    phone_alternate: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(100), default='Pakistan')
    marital_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    occupation: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    profile_photo: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_vip: Mapped[bool] = mapped_column(Boolean, default=False)
    credit_limit: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    family_members: Mapped[List["CustomerFamilyMember"]] = relationship(back_populates="customer", cascade="all, delete-orphan")
    emergency_contacts: Mapped[List["CustomerEmergencyContact"]] = relationship(back_populates="customer", cascade="all, delete-orphan")
    
    flight_bookings: Mapped[List["FlightBooking"]] = relationship("FlightBooking", back_populates="customer")
    visa_applications: Mapped[List["VisaApplication"]] = relationship("VisaApplication", back_populates="customer")
    hotel_bookings: Mapped[List["HotelBooking"]] = relationship("HotelBooking", back_populates="customer")
    tour_bookings: Mapped[List["TourBooking"]] = relationship("TourBooking", back_populates="customer")
    umrah_bookings: Mapped[List["CustomUmrahBooking"]] = relationship("CustomUmrahBooking", back_populates="customer")
    hajj_pilgrims: Mapped[List["HajjPilgrim"]] = relationship("HajjPilgrim", back_populates="customer")
    transport_bookings: Mapped[List["TransportBooking"]] = relationship("TransportBooking", back_populates="customer")
    invoices: Mapped[List["Invoice"]] = relationship("Invoice", back_populates="customer")
    receipts: Mapped[List["Receipt"]] = relationship("Receipt", back_populates="customer")

    @property
    def full_name(self) -> str:
        return f"{self.title or ''} {self.first_name} {self.last_name}".strip()

    def __repr__(self) -> str:
        return f"<Customer {self.customer_code} {self.full_name}>"


class CustomerFamilyMember(BaseModel):
    __tablename__ = 'customer_family_members'

    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey('customers.id'), index=True, nullable=False)
    relation: Mapped[str] = mapped_column(String(50), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    age: Mapped[Optional[int]] = mapped_column(nullable=True)  # convenience field; use date_of_birth for precision
    cnic: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    passport_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    passport_expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    customer: Mapped["Customer"] = relationship(back_populates="family_members")

    def __repr__(self) -> str:
        return f"<CustomerFamilyMember {self.full_name}>"


class CustomerEmergencyContact(BaseModel):
    __tablename__ = 'customer_emergency_contacts'

    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey('customers.id'), index=True, nullable=False)
    contact_name: Mapped[str] = mapped_column(String(200), nullable=False)
    relation: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    customer: Mapped["Customer"] = relationship(back_populates="emergency_contacts")

    def __repr__(self) -> str:
        return f"<CustomerEmergencyContact {self.contact_name}>"
