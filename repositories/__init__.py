"""
Repositories Module
Contains all data access layer classes implementing the Repository Pattern.
"""
from .customer_repository import CustomerRepository, CustomerFamilyMemberRepository, CustomerEmergencyContactRepository
from .flight_repository import FlightBookingRepository, FlightPassengerRepository
from .visa_repository import VisaApplicationRepository, VisaApplicantRepository
from .accounting_repository import (
    InvoiceRepository, ReceiptRepository, ExpenseRepository, 
    JournalEntryRepository, ChartOfAccountRepository
)
from .user_repository import UserRepository, ActivityLogRepository
from .employee_repository import EmployeeRepository, AttendanceRepository, SalaryRecordRepository
from .umrah_repository import UmrahPackageTemplateRepository, CustomUmrahBookingRepository, UmrahPilgrimRepository
from .hotel_repository import HotelRepository, HotelBookingRepository

__all__ = [
    "CustomerRepository", "CustomerFamilyMemberRepository", "CustomerEmergencyContactRepository",
    "FlightBookingRepository", "FlightPassengerRepository",
    "VisaApplicationRepository", "VisaApplicantRepository",
    "InvoiceRepository", "ReceiptRepository", "ExpenseRepository", "JournalEntryRepository", "ChartOfAccountRepository",
    "UserRepository", "ActivityLogRepository",
    "EmployeeRepository", "AttendanceRepository", "SalaryRecordRepository",
    "UmrahPackageTemplateRepository", "CustomUmrahBookingRepository", "UmrahPilgrimRepository",
    "HotelRepository", "HotelBookingRepository"
]
