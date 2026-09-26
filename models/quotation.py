from datetime import date, timedelta
from typing import List, Optional

from sqlalchemy import String, Numeric, Date, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.base_model import BaseModel


def _default_valid_until() -> date:
    """Return the default expiration date (7 days from today)."""
    return date.today() + timedelta(days=7)


class Quotation(BaseModel):
    """
    Represents an estimate/quote provided to either a walk-in guest or an existing customer.
    Does not impact ledgers or CRM reporting.
    """
    __tablename__ = 'quotations'

    date_created: Mapped[date] = mapped_column(
        Date, 
        default=date.today, 
        nullable=False,
        doc="The date the quotation was generated."
    )
    valid_until: Mapped[date] = mapped_column(
        Date, 
        default=_default_valid_until, 
        nullable=False,
        doc="The expiration date for the quoted prices."
    )
    
    # Walk-in details
    guest_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    guest_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Optional link to an existing registered customer
    customer_id: Mapped[Optional[str]] = mapped_column(
        String(36), 
        ForeignKey('customers.id'), 
        nullable=True,
        index=True
    )
    
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0, nullable=False)
    
    # 'Pending', 'Accepted', 'Expired'
    status: Mapped[str] = mapped_column(String(20), default='Pending', nullable=False)
    
    # Relationships
    items: Mapped[List["QuotationItem"]] = relationship(
        "QuotationItem", 
        back_populates="quotation",
        cascade="all, delete-orphan"
    )


class QuotationItem(BaseModel):
    """
    A single service line item inside a Quotation.
    """
    __tablename__ = 'quotation_items'

    quotation_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey('quotations.id'), 
        nullable=False,
        index=True
    )
    
    service_description: Mapped[str] = mapped_column(Text, nullable=False)
    qty: Mapped[int] = mapped_column(default=1, nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0, nullable=False)
    total: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0, nullable=False)

    # Relationships
    quotation: Mapped["Quotation"] = relationship(
        "Quotation", 
        back_populates="items"
    )
