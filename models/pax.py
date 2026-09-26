"""
models/pax.py
=============
Passenger (PAX) model for the TAMS centralized booking system.

Each Pax record represents one traveller attached to a master Booking.
The ``pax_type`` column categorises the traveller as an Adult, Child, or
Infant so that the pricing matrix on the Booking can be applied correctly
when generating invoices and profit reports.
"""

import enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, Boolean, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.base_model import BaseModel

if TYPE_CHECKING:
    from models.booking import Booking
    from models.customer import Customer


class PaxType(str, enum.Enum):
    """Categorical classification for a single traveller."""

    ADULT = "Adult"
    CHILD = "Child"
    INFANT = "Infant"


class Pax(BaseModel):
    """
    Represents a single traveller (passenger) within a group booking.

    Attributes
    ----------
    booking_id:
        Foreign key back to the master ``Booking`` record.
    pax_type:
        Categorical classification — Adult / Child / Infant.
        Determines which pricing tier is applied on the parent Booking.
    first_name / last_name:
        Legal name as it appears on travel documents.
    passport_number:
        Passport number (nullable for domestic-only itineraries).
    cnic:
        Pakistani CNIC (nullable for foreign nationals).
    date_of_birth:
        Date of birth — also used to infer ``pax_type`` when not set
        explicitly.
    is_group_leader:
        True for the primary contact within a group booking.
    linked_customer_id:
        Optional link to an existing ``Customer`` record (e.g. when the
        group leader is a registered customer).
    """

    __tablename__ = "pax"

    # ------------------------------------------------------------------ #
    # Foreign keys                                                         #
    # ------------------------------------------------------------------ #
    booking_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("bookings.id"),
        index=True,
        nullable=False,
        doc="FK — parent master booking.",
    )

    # ------------------------------------------------------------------ #
    # Categorical classification                                           #
    # ------------------------------------------------------------------ #
    pax_type: Mapped[str] = mapped_column(
        Enum(
            PaxType.ADULT.value,
            PaxType.CHILD.value,
            PaxType.INFANT.value,
            name="pax_type_enum",
        ),
        nullable=False,
        default=PaxType.ADULT.value,
        server_default=PaxType.ADULT.value,
        doc="Traveller category — Adult, Child, or Infant.",
    )

    # ------------------------------------------------------------------ #
    # Personal details                                                     #
    # ------------------------------------------------------------------ #
    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Given name(s) as on travel document.",
    )
    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Family / surname as on travel document.",
    )
    passport_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        doc="Passport number (nullable for domestic itineraries).",
    )
    cnic: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        doc="Pakistani CNIC (nullable for foreign nationals).",
    )
    date_of_birth: Mapped[Optional[Date]] = mapped_column(
        Date,
        nullable=True,
        doc="Date of birth.",
    )

    # ------------------------------------------------------------------ #
    # Group leader logic                                                   #
    # ------------------------------------------------------------------ #
    is_group_leader: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        doc="True if this PAX is the billing / contact leader of the group.",
    )
    linked_customer_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("customers.id"),
        nullable=True,
        doc="Optional FK to a registered Customer record.",
    )

    # ------------------------------------------------------------------ #
    # Relationships                                                        #
    # ------------------------------------------------------------------ #
    booking: Mapped["Booking"] = relationship(
        "Booking",
        back_populates="passengers",
    )
    linked_customer: Mapped[Optional["Customer"]] = relationship("Customer")

    # ------------------------------------------------------------------ #
    # Dunder                                                               #
    # ------------------------------------------------------------------ #
    def __repr__(self) -> str:
        return (
            f"<Pax {self.first_name} {self.last_name}"
            f" [{self.pax_type}]>"
        )
