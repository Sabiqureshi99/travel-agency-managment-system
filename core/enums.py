"""
core/enums.py
=============
Application-wide enumerations used across models, services, and UI.

All enums use string values so they serialise/display cleanly in the UI
and database without needing extra mapping.
"""
from enum import Enum


# ---------------------------------------------------------------------------
# Users & Auth
# ---------------------------------------------------------------------------

class UserRole(str, Enum):
    """Top-level user roles."""
    ADMIN = "Admin"
    OWNER = "Owner"
    EMPLOYEE = "Employee"


class UserStatus(str, Enum):
    """Account status."""
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    LOCKED = "Locked"


# ---------------------------------------------------------------------------
# Permissions
# ---------------------------------------------------------------------------

class PermissionAction(str, Enum):
    """Granular permission actions available per module."""
    VIEW = "view"
    ADD = "add"
    EDIT = "edit"
    DELETE = "delete"
    PRINT = "print"
    EXPORT = "export"


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------

class Gender(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"


class MaritalStatus(str, Enum):
    SINGLE = "Single"
    MARRIED = "Married"
    DIVORCED = "Divorced"
    WIDOWED = "Widowed"


class CustomerType(str, Enum):
    INDIVIDUAL = "Individual"
    CORPORATE = "Corporate"
    VIP = "VIP"


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------

class DocumentType(str, Enum):
    PASSPORT = "Passport"
    CNIC = "CNIC"
    VISA = "Visa"
    TICKET = "Ticket"
    HOTEL_VOUCHER = "Hotel Voucher"
    INVOICE = "Invoice"
    RECEIPT = "Receipt"
    INSURANCE = "Insurance"
    OTHER = "Other"


# ---------------------------------------------------------------------------
# Flights
# ---------------------------------------------------------------------------

class FlightType(str, Enum):
    DOMESTIC = "Domestic"
    INTERNATIONAL = "International"


class TripType(str, Enum):
    ONE_WAY = "One Way"
    RETURN = "Return"
    MULTI_CITY = "Multi City"


class CabinClass(str, Enum):
    ECONOMY = "Economy"
    PREMIUM_ECONOMY = "Premium Economy"
    BUSINESS = "Business"
    FIRST = "First"


class BookingStatus(str, Enum):
    PENDING = "Pending"
    CONFIRMED = "Confirmed"
    CANCELLED = "Cancelled"
    REFUNDED = "Refunded"
    COMPLETED = "Completed"
    ON_HOLD = "On Hold"


class TicketStatus(str, Enum):
    ISSUED = "Issued"
    REISSUED = "Reissued"
    CANCELLED = "Cancelled"
    REFUNDED = "Refunded"
    VOID = "Void"


# ---------------------------------------------------------------------------
# Visa
# ---------------------------------------------------------------------------

class VisaType(str, Enum):
    TOURIST = "Tourist"
    BUSINESS = "Business"
    TRANSIT = "Transit"
    STUDENT = "Student"
    WORK = "Work"
    RESIDENCE = "Residence"
    UMRAH = "Umrah"
    HAJJ = "Hajj"
    FAMILY = "Family Visit"
    MEDICAL = "Medical"


class VisaStatus(str, Enum):
    APPLIED = "Applied"
    PENDING = "Pending"
    APPOINTMENT = "Appointment Scheduled"
    SUBMITTED = "Submitted"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    COLLECTED = "Collected"
    EXPIRED = "Expired"
    CANCELLED = "Cancelled"


# ---------------------------------------------------------------------------
# Umrah & Hajj
# ---------------------------------------------------------------------------

class UmrahPackageType(str, Enum):
    ECONOMY = "Economy"
    STANDARD = "Standard"
    PREMIUM = "Premium"
    VIP = "VIP"
    CUSTOM = "Custom"


class RoomSharingType(str, Enum):
    SINGLE = "Single"
    DOUBLE = "Double"
    TRIPLE = "Triple"
    QUAD = "Quad"
    QUINT = "Quint"


class PilgrimStatus(str, Enum):
    REGISTERED = "Registered"
    CONFIRMED = "Confirmed"
    DEPARTED = "Departed"
    RETURNED = "Returned"
    CANCELLED = "Cancelled"


class HajjApplicationType(str, Enum):
    GOVERNMENT = "Government Scheme"
    PRIVATE = "Private"


# ---------------------------------------------------------------------------
# Hotels
# ---------------------------------------------------------------------------

class RoomType(str, Enum):
    SINGLE = "Single"
    DOUBLE = "Double"
    TWIN = "Twin"
    TRIPLE = "Triple"
    SUITE = "Suite"
    DELUXE = "Deluxe"


class HotelBookingStatus(str, Enum):
    INQUIRY = "Inquiry"
    CONFIRMED = "Confirmed"
    CHECKED_IN = "Checked In"
    CHECKED_OUT = "Checked Out"
    CANCELLED = "Cancelled"
    NO_SHOW = "No Show"


# ---------------------------------------------------------------------------
# Transport
# ---------------------------------------------------------------------------

class VehicleType(str, Enum):
    CAR = "Car"
    VAN = "Van"
    BUS = "Bus"
    COASTER = "Coaster"
    HIACE = "Hiace"
    LUXURY_BUS = "Luxury Bus"


class VehicleStatus(str, Enum):
    AVAILABLE = "Available"
    IN_USE = "In Use"
    MAINTENANCE = "Under Maintenance"
    RETIRED = "Retired"


# ---------------------------------------------------------------------------
# Vendors
# ---------------------------------------------------------------------------

class VendorType(str, Enum):
    AIRLINE = "Airline"
    HOTEL = "Hotel"
    VISA_AGENT = "Visa Agent"
    TRANSPORT = "Transport"
    TOUR_OPERATOR = "Tour Operator"
    INSURANCE = "Insurance"
    OTHER = "Other"


# ---------------------------------------------------------------------------
# Accounting
# ---------------------------------------------------------------------------

class AccountType(str, Enum):
    ASSET = "Asset"
    LIABILITY = "Liability"
    EQUITY = "Equity"
    INCOME = "Income"
    EXPENSE = "Expense"


class AccountSubType(str, Enum):
    CASH = "Cash"
    BANK = "Bank"
    RECEIVABLE = "Accounts Receivable"
    PAYABLE = "Accounts Payable"
    INVENTORY = "Inventory"
    FIXED_ASSET = "Fixed Asset"
    SALES = "Sales"
    COST_OF_SALES = "Cost of Sales"
    OPERATING_EXPENSE = "Operating Expense"
    TAX = "Tax"
    OTHER = "Other"


class JournalEntryType(str, Enum):
    SALE = "Sale"
    PURCHASE = "Purchase"
    RECEIPT = "Receipt"
    PAYMENT = "Payment"
    JOURNAL = "Journal"
    OPENING = "Opening Balance"
    ADJUSTMENT = "Adjustment"


class PaymentMethod(str, Enum):
    CASH = "Cash"
    BANK_TRANSFER = "Bank Transfer"
    CHEQUE = "Cheque"
    CREDIT_CARD = "Credit Card"
    ONLINE = "Online Transfer"
    MOBILE_BANKING = "Mobile Banking"


class InvoiceStatus(str, Enum):
    DRAFT = "Draft"
    SENT = "Sent"
    PARTIALLY_PAID = "Partially Paid"
    PAID = "Paid"
    OVERDUE = "Overdue"
    CANCELLED = "Cancelled"


# ---------------------------------------------------------------------------
# Currency
# ---------------------------------------------------------------------------

class Currency(str, Enum):
    PKR = "PKR"
    SAR = "SAR"
    USD = "USD"


# ---------------------------------------------------------------------------
# General
# ---------------------------------------------------------------------------

class AttendanceStatus(str, Enum):
    PRESENT = "Present"
    ABSENT = "Absent"
    LATE = "Late"
    HALF_DAY = "Half Day"
    LEAVE = "Leave"
    HOLIDAY = "Holiday"


class LeaveType(str, Enum):
    ANNUAL = "Annual Leave"
    SICK = "Sick Leave"
    CASUAL = "Casual Leave"
    UNPAID = "Unpaid Leave"
    HAJJ = "Hajj Leave"


class SalaryType(str, Enum):
    MONTHLY = "Monthly"
    DAILY = "Daily"
    COMMISSION = "Commission Based"


class TourPackageType(str, Enum):
    DOMESTIC = "Domestic"
    INTERNATIONAL = "International"
    CUSTOM = "Custom"


class NotificationPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class ReportFormat(str, Enum):
    PDF = "PDF"
    EXCEL = "Excel"
    CSV = "CSV"
