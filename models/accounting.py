"""
models/accounting.py
=====================
SQLAlchemy ORM models for the double-entry accounting module.

Models:
    - ChartOfAccount  — account tree (assets, liabilities, income, expenses)
    - JournalEntry    — accounting transaction header
    - JournalLine     — individual debit/credit line of a journal entry
    - Invoice         — customer invoice with line items
    - InvoiceItem     — single line item on an invoice
    - Receipt         — payment received from a customer
    - Expense         — business expense record
"""
from __future__ import annotations

from datetime import date
from typing import List, Optional

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.base_model import BaseModel
import enum

class PaymentSource(str, enum.Enum):
    CASH = "Cash"
    BANK = "Bank"


class ChartOfAccount(BaseModel):
    """
    A node in the Chart of Accounts tree.

    Supports unlimited hierarchy via self-referential parent/children.
    Only leaf nodes (is_leaf=True) should have journal entries posted.
    """

    __tablename__ = "chart_of_accounts"

    account_code: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False
    )
    account_name: Mapped[str] = mapped_column(String(200), nullable=False)
    account_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # Asset, Liability, Equity, Income, Expense

    # Hierarchy
    parent_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("chart_of_accounts.id"), nullable=True, index=True
    )

    # Leaf/bank flags
    is_leaf: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_bank_account: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # Financial
    currency: Mapped[str] = mapped_column(String(10), default="PKR", nullable=False)
    opening_balance: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="Active", nullable=False)

    # Relationships (self-referential)
    children: Mapped[List["ChartOfAccount"]] = relationship(
        "ChartOfAccount",
        back_populates="parent",
        foreign_keys=[parent_id],
        cascade="all, delete-orphan",
    )
    parent: Mapped[Optional["ChartOfAccount"]] = relationship(
        "ChartOfAccount",
        back_populates="children",
        foreign_keys=[parent_id],
        remote_side="ChartOfAccount.id",
    )
    journal_lines: Mapped[List["JournalLine"]] = relationship(
        "JournalLine", back_populates="account"
    )

    def __repr__(self) -> str:
        return f"<ChartOfAccount {self.account_code} — {self.account_name}>"


class JournalEntry(BaseModel):
    """
    An accounting transaction header.

    A journal entry must be balanced: sum(debits) == sum(credits) across
    all its JournalLine children.
    """

    __tablename__ = "journal_entries"

    entry_number: Mapped[str] = mapped_column(
        String(30), unique=True, index=True, nullable=False
    )
    entry_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    entry_type: Mapped[str] = mapped_column(
        String(30), default="General", nullable=False
    )  # General, Invoice, Receipt, Expense, etc.
    reference_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # Invoice, Receipt, Expense …
    reference_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_posted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="Draft", nullable=False)

    lines: Mapped[List["JournalLine"]] = relationship(
        back_populates="journal_entry", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<JournalEntry {self.entry_number} [{self.status}]>"


class JournalLine(BaseModel):
    """A single debit or credit line within a JournalEntry."""

    __tablename__ = "journal_lines"

    journal_entry_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("journal_entries.id"), index=True, nullable=False
    )
    account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("chart_of_accounts.id"), index=True, nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    debit_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    credit_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    journal_entry: Mapped["JournalEntry"] = relationship(back_populates="lines")
    account: Mapped["ChartOfAccount"] = relationship(back_populates="journal_lines")

    def __repr__(self) -> str:
        return (
            f"<JournalLine account={self.account_id} "
            f"dr={self.debit_amount} cr={self.credit_amount}>"
        )


class Invoice(BaseModel):
    """Customer invoice with line items."""

    __tablename__ = "invoices"

    invoice_number: Mapped[str] = mapped_column(
        String(30), unique=True, index=True, nullable=False
    )
    customer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("customers.id"), index=True, nullable=False
    )
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    reference_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # FlightBooking, VisaApplication …
    reference_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    group_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    discount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    tax_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    service_charges: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    amount_paid: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    amount_remaining: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    currency: Mapped[str] = mapped_column(String(10), default="PKR", nullable=False)

    status: Mapped[str] = mapped_column(
        String(30), default="Unpaid", nullable=False
    )  # Unpaid, Partial, Paid, Cancelled
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="invoices")  # type: ignore[name-defined]
    items: Mapped[List["InvoiceItem"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan"
    )
    receipts: Mapped[List["Receipt"]] = relationship(back_populates="invoice", cascade="all, delete-orphan")
    payment_transactions: Mapped[List["PaymentTransaction"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan"
    )

    @property
    def balance_due(self) -> float:
        return float(self.amount_remaining)
        
    @balance_due.setter
    def balance_due(self, value: float):
        self.amount_remaining = value

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number} [{self.status}]>"


class InvoiceItem(BaseModel):
    """A single line item on an Invoice."""

    __tablename__ = "invoice_items"

    invoice_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("invoices.id"), index=True, nullable=False
    )
    description: Mapped[str] = mapped_column(String(300), nullable=False)
    passenger_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    passport_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    total_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    invoice: Mapped["Invoice"] = relationship(back_populates="items")

    def __repr__(self) -> str:
        return f"<InvoiceItem '{self.description}' qty={self.quantity}>"


class Receipt(BaseModel):
    """A payment received from a customer."""

    __tablename__ = "receipts"

    receipt_number: Mapped[str] = mapped_column(
        String(30), unique=True, index=True, nullable=False
    )
    customer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("customers.id"), index=True, nullable=False
    )
    invoice_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("invoices.id"), nullable=True
    )
    bank_account_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("chart_of_accounts.id"), nullable=True
    )
    receipt_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    payment_method: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # Cash, Bank Transfer, Cheque, Card
    payment_source: Mapped[PaymentSource] = mapped_column(
        Enum(PaymentSource, name="payment_source_enum"), 
        nullable=False, 
        default=PaymentSource.CASH
    )
    bank_account_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    reference_number: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    currency: Mapped[str] = mapped_column(String(10), default="PKR", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="receipts")  # type: ignore[name-defined]
    invoice: Mapped[Optional["Invoice"]] = relationship(back_populates="receipts")

    def __repr__(self) -> str:
        return f"<Receipt {self.receipt_number} amount={self.amount}>"


class Expense(BaseModel):
    """A business expense record with optional reference to a vendor."""

    __tablename__ = "expenses"

    expense_number: Mapped[str] = mapped_column(
        String(30), unique=True, index=True, nullable=False
    )
    account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("chart_of_accounts.id"), nullable=False, index=True
    )
    payment_account_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("chart_of_accounts.id"), nullable=True
    )  # Cash/Bank account used for payment
    expense_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="PKR", nullable=False)
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)
    reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), default="Approved", nullable=False
    )
    payment_source: Mapped[PaymentSource] = mapped_column(
        Enum(PaymentSource, name="payment_source_enum"), 
        nullable=False, 
        default=PaymentSource.CASH
    )
    bank_account_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    account: Mapped["ChartOfAccount"] = relationship(
        "ChartOfAccount", foreign_keys=[account_id]
    )
    payment_account: Mapped[Optional["ChartOfAccount"]] = relationship(
        "ChartOfAccount", foreign_keys=[payment_account_id]
    )

    def __repr__(self) -> str:
        return f"<Expense {self.expense_number} amount={self.amount}>"


class PaymentTransaction(BaseModel):
    """A payment ledger transaction for an Invoice."""

    __tablename__ = "payment_transactions"

    transaction_number: Mapped[str] = mapped_column(
        String(30), unique=True, index=True, nullable=False
    )
    invoice_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("invoices.id"), index=True, nullable=False
    )
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    payment_method: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # Cash, Bank Transfer, Cheque, Card
    reference_number: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    invoice: Mapped["Invoice"] = relationship(back_populates="payment_transactions")

    def __repr__(self) -> str:
        return f"<PaymentTransaction {self.transaction_number} amount={self.amount}>"


class VendorPayment(BaseModel):
    """Payment made to a vendor/vendor."""
    __tablename__ = "vendor_payments"

    payment_number: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    vendor_name: Mapped[str] = mapped_column(String(200), nullable=False)
    vendor_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey('vendors.id'), nullable=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)
    payment_source: Mapped[PaymentSource] = mapped_column(
        Enum(PaymentSource, name="payment_source_enum"), 
        nullable=False, 
        default=PaymentSource.BANK
    )
    bank_account_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    reference_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    vendor: Mapped[Optional["Vendor"]] = relationship("Vendor", back_populates="vendor_payments")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<VendorPayment {self.payment_number} to {self.vendor_name} for {self.amount}>"


class Withdrawal(BaseModel):
    """Owner cash drawing or profit withdrawal."""
    __tablename__ = "withdrawals"

    withdrawal_number: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Withdrawal {self.withdrawal_number} for {self.amount}>"


class InternalTransfer(BaseModel):
    """Handles routing of physical Cash to Bank Accounts."""
    __tablename__ = "internal_transfers"

    transfer_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="Cash")
    destination: Mapped[str] = mapped_column(String(50), nullable=False, default="Bank")
    
    destination_bank_account: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Specific bank (e.g. Meezan Bank)"
    )
    reference_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    processed_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    def __repr__(self) -> str:
        return f"<InternalTransfer {self.amount:,.2f} Cash -> Bank on {self.transfer_date}>"

