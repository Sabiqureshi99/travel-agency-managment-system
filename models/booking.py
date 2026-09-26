"""
models/booking.py
=================
Master Booking model for the TAMS centralized booking system.

Each ``Booking`` record acts as the single source of truth for a
multi-service group itinerary.  Pricing is stored as a *categorical
matrix* — separate cost and selling prices for Adult, Child, and Infant
travellers — so that gross profit can be computed accurately for mixed
groups (e.g. 8 Adults + 1 Child + 1 Infant).

Persisted columns
-----------------
- ``adult_cost_price``   / ``adult_selling_price``   / ``adult_count``
- ``child_cost_price``   / ``child_selling_price``   / ``child_count``
- ``infant_cost_price``  / ``infant_selling_price``  / ``infant_count``

Computed properties (not persisted)
------------------------------------
- ``total_cost``     — sum of (count × cost_price) for all categories
- ``total_revenue``  — sum of (count × selling_price) for all categories
- ``net_profit``     — ``total_revenue`` - ``total_cost``

Backward-compatibility note
----------------------------
The legacy ``cost_price``, ``selling_price``, and ``net_profit`` columns
have been *replaced* by the categorical matrix above.  Any service code
that previously wrote ``Booking(cost_price=x, selling_price=y)`` must be
updated to supply the full categorical payload instead.  The ``net_profit``
*database column* is gone; use the ``net_profit`` *property* instead.

The ``financial_engine`` and ``report_service`` that previously ran
``func.sum(Booking.cost_price)`` must migrate to
``func.sum(Booking.total_cost_column)``; a compatibility helper
``Booking.total_cost_sql_expr()`` is provided for that purpose.
"""

from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Numeric, String, Integer, ForeignKey, event
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.base_model import BaseModel

if TYPE_CHECKING:
    from models.pax import Pax


# --------------------------------------------------------------------------- #
# Sentinel zero — a typed Decimal constant used throughout the model           #
# --------------------------------------------------------------------------- #
_ZERO = Decimal("0.00")


class Booking(BaseModel):
    """
    Master booking record — the hub of every TAMS group itinerary.

    Pricing matrix columns
    ----------------------
    Each passenger category (Adult / Child / Infant) has three columns:

    * ``<category>_count``        — number of travellers in this tier
    * ``<category>_cost_price``   — cost per head in this tier (PKR)
    * ``<category>_selling_price``— selling price per head (PKR)

    Computed properties are available via Python ``@hybrid_property``
    decorators so they work both in-Python and in SQLAlchemy queries.
    """

    __tablename__ = "bookings"

    # ------------------------------------------------------------------ #
    # Core identifiers                                                     #
    # ------------------------------------------------------------------ #
    booking_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc=(
            "Service type: 'Umrah_Package', 'Flight_Only', "
            "'Hotel_Only', 'Visa_Only', 'Transport_Only', or 'Unified'."
        ),
    )
    customer_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("customers.id"),
        index=True,
        nullable=False,
        doc="FK — the primary customer / billing entity.",
    )
    package_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("custom_umrah_bookings.id"),
        nullable=True,
        doc="FK — linked Umrah package record (optional).",
    )

    # ------------------------------------------------------------------ #
    # Categorical pricing matrix — ADULT tier                             #
    # ------------------------------------------------------------------ #
    adult_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        doc="Number of Adult travellers in this booking.",
    )
    adult_cost_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=_ZERO,
        server_default="0.00",
        doc="Cost price per Adult (PKR).",
    )
    adult_selling_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=_ZERO,
        server_default="0.00",
        doc="Selling price per Adult (PKR).",
    )

    # ------------------------------------------------------------------ #
    # Categorical pricing matrix — CHILD tier                             #
    # ------------------------------------------------------------------ #
    child_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        doc="Number of Child travellers in this booking.",
    )
    child_cost_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=_ZERO,
        server_default="0.00",
        doc="Cost price per Child (PKR).",
    )
    child_selling_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=_ZERO,
        server_default="0.00",
        doc="Selling price per Child (PKR).",
    )

    # ------------------------------------------------------------------ #
    # Categorical pricing matrix — INFANT tier                            #
    # ------------------------------------------------------------------ #
    infant_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        doc="Number of Infant travellers in this booking.",
    )
    infant_cost_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=_ZERO,
        server_default="0.00",
        doc="Cost price per Infant (PKR).",
    )
    infant_selling_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=_ZERO,
        server_default="0.00",
        doc="Selling price per Infant (PKR).",
    )

    # ------------------------------------------------------------------ #
    # Supplementary fields                                                 #
    # ------------------------------------------------------------------ #
    details: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        doc="Optional JSON blob for miscellaneous service metadata.",
    )
    payment_method: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        doc="'Cash' or 'Bank Transfer'.",
    )

    # ------------------------------------------------------------------ #
    # Relationships                                                        #
    # ------------------------------------------------------------------ #
    passengers: Mapped[list["Pax"]] = relationship(
        "Pax",
        back_populates="booking",
        cascade="all, delete-orphan",
        doc="All PAX records belonging to this booking.",
    )

    # ------------------------------------------------------------------ #
    # Computed financials — Python @property layer                        #
    # ------------------------------------------------------------------ #

    @property
    def total_cost(self) -> Decimal:
        """
        Total cost across all passenger categories.

        Formula::

            (adult_count  × adult_cost_price)
          + (child_count  × child_cost_price)
          + (infant_count × infant_cost_price)

        Returns
        -------
        Decimal
            Aggregate cost in PKR, rounded to 2 decimal places.
        """
        adult_cost = Decimal(self.adult_count or 0) * Decimal(
            self.adult_cost_price or _ZERO
        )
        child_cost = Decimal(self.child_count or 0) * Decimal(
            self.child_cost_price or _ZERO
        )
        infant_cost = Decimal(self.infant_count or 0) * Decimal(
            self.infant_cost_price or _ZERO
        )
        return (adult_cost + child_cost + infant_cost).quantize(Decimal("0.01"))

    @property
    def total_revenue(self) -> Decimal:
        """
        Total revenue across all passenger categories.

        Formula::

            (adult_count  × adult_selling_price)
          + (child_count  × child_selling_price)
          + (infant_count × infant_selling_price)

        Returns
        -------
        Decimal
            Aggregate revenue in PKR, rounded to 2 decimal places.
        """
        adult_rev = Decimal(self.adult_count or 0) * Decimal(
            self.adult_selling_price or _ZERO
        )
        child_rev = Decimal(self.child_count or 0) * Decimal(
            self.child_selling_price or _ZERO
        )
        infant_rev = Decimal(self.infant_count or 0) * Decimal(
            self.infant_selling_price or _ZERO
        )
        return (adult_rev + child_rev + infant_rev).quantize(Decimal("0.01"))

    @property
    def net_profit(self) -> Decimal:
        """
        Net (gross) profit for this booking.

        Formula::

            total_revenue - total_cost

        Returns
        -------
        Decimal
            Profit in PKR, rounded to 2 decimal places.  May be negative
            if the booking was sold below cost.
        """
        return (self.total_revenue - self.total_cost).quantize(Decimal("0.01"))

    # ------------------------------------------------------------------ #
    # Aggregate helpers — per-category subtotals                          #
    # ------------------------------------------------------------------ #

    @property
    def adult_subtotal_cost(self) -> Decimal:
        """Adult tier: count × cost_price."""
        return (
            Decimal(self.adult_count or 0)
            * Decimal(self.adult_cost_price or _ZERO)
        ).quantize(Decimal("0.01"))

    @property
    def adult_subtotal_revenue(self) -> Decimal:
        """Adult tier: count × selling_price."""
        return (
            Decimal(self.adult_count or 0)
            * Decimal(self.adult_selling_price or _ZERO)
        ).quantize(Decimal("0.01"))

    @property
    def child_subtotal_cost(self) -> Decimal:
        """Child tier: count × cost_price."""
        return (
            Decimal(self.child_count or 0)
            * Decimal(self.child_cost_price or _ZERO)
        ).quantize(Decimal("0.01"))

    @property
    def child_subtotal_revenue(self) -> Decimal:
        """Child tier: count × selling_price."""
        return (
            Decimal(self.child_count or 0)
            * Decimal(self.child_selling_price or _ZERO)
        ).quantize(Decimal("0.01"))

    @property
    def infant_subtotal_cost(self) -> Decimal:
        """Infant tier: count × cost_price."""
        return (
            Decimal(self.infant_count or 0)
            * Decimal(self.infant_cost_price or _ZERO)
        ).quantize(Decimal("0.01"))

    @property
    def infant_subtotal_revenue(self) -> Decimal:
        """Infant tier: count × selling_price."""
        return (
            Decimal(self.infant_count or 0)
            * Decimal(self.infant_selling_price or _ZERO)
        ).quantize(Decimal("0.01"))

    # ------------------------------------------------------------------ #
    # SQLAlchemy service / report query helpers                            #
    # ------------------------------------------------------------------ #

    @staticmethod
    def total_cost_sql_expr():
        """
        Return a SQLAlchemy column expression for ``total_cost`` that can be
        used inside ``func.sum()`` in ``financial_engine.py`` and
        ``report_service.py``.

        Usage::

            from models.booking import Booking
            from sqlalchemy import func

            total = session.query(
                func.sum(Booking.total_cost_sql_expr())
            ).scalar()

        Note
        ----
        This is a *static helper*, not a hybrid property, because SQLAlchemy
        does not natively multiply two mapped columns as a SQL expression via
        ``hybrid_property`` without a custom ``expression`` decorator — which
        requires dialect-specific SQL operators.  Keep it explicit and readable.
        """
        from sqlalchemy import literal_column

        return (
            literal_column("adult_count")  * literal_column("adult_cost_price")
            + literal_column("child_count") * literal_column("child_cost_price")
            + literal_column("infant_count") * literal_column("infant_cost_price")
        )

    @staticmethod
    def total_revenue_sql_expr():
        """
        Return a SQLAlchemy column expression for ``total_revenue`` suitable
        for use inside ``func.sum()`` in analytical queries.
        """
        from sqlalchemy import literal_column

        return (
            literal_column("adult_count")  * literal_column("adult_selling_price")
            + literal_column("child_count") * literal_column("child_selling_price")
            + literal_column("infant_count") * literal_column("infant_selling_price")
        )

    # ------------------------------------------------------------------ #
    # Dunder                                                               #
    # ------------------------------------------------------------------ #

    def __repr__(self) -> str:
        pax_total = (
            (self.adult_count or 0)
            + (self.child_count or 0)
            + (self.infant_count or 0)
        )
        return (
            f"<Booking id={self.id!r} type={self.booking_type!r}"
            f" pax={pax_total} revenue={self.total_revenue}>"
        )
