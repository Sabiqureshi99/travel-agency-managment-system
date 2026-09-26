from typing import Optional, List
from datetime import date
from sqlalchemy import String, Integer, Date, Text, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.base_model import BaseModel

class HajjGroup(BaseModel):
    __tablename__ = 'hajj_groups'

    group_code: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    group_name: Mapped[str] = mapped_column(String(300), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    application_type: Mapped[str] = mapped_column(String(30), default='Private')
    total_quota: Mapped[int] = mapped_column(Integer, default=0)
    filled_seats: Mapped[int] = mapped_column(Integer, default=0)
    package_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    currency: Mapped[str] = mapped_column(String(10), default='PKR')
    departure_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    return_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    mina_building: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    makkah_hotel: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    madinah_hotel: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default='Open')
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    pilgrims: Mapped[List["HajjPilgrim"]] = relationship(back_populates="group", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<HajjGroup {self.group_code}>"


class HajjPilgrim(BaseModel):
    __tablename__ = 'hajj_pilgrims'

    group_id: Mapped[str] = mapped_column(String(36), ForeignKey('hajj_groups.id'), index=True, nullable=False)
    customer_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey('customers.id'), nullable=True)
    serial_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    father_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    passport_number: Mapped[str] = mapped_column(String(50), nullable=False)
    passport_expiry: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    mehram_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    mehram_relation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    application_status: Mapped[str] = mapped_column(String(30), default='Registered')
    amount_paid: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    amount_remaining: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    group: Mapped["HajjGroup"] = relationship(back_populates="pilgrims")
    customer: Mapped[Optional["Customer"]] = relationship("Customer", back_populates="hajj_pilgrims")

    def __repr__(self) -> str:
        return f"<HajjPilgrim {self.full_name}>"
