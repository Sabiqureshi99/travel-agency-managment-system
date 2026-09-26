from typing import Optional, List
from datetime import date, datetime
from sqlalchemy import String, Boolean, Date, DateTime, Text, Numeric, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.base_model import BaseModel

class Employee(BaseModel):
    __tablename__ = 'employees'

    employee_code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey('users.id'), nullable=True, unique=True)
    title: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    father_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    cnic: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    designation: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    date_joined: Mapped[date] = mapped_column(Date, nullable=False)
    date_left: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    salary_type: Mapped[str] = mapped_column(String(20), default='Monthly')
    base_salary: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    profile_photo: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    bank_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    bank_account_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default='Active')

    user: Mapped[Optional["User"]] = relationship("User")
    attendance_records: Mapped[List["Attendance"]] = relationship(back_populates="employee", cascade="all, delete-orphan")
    salary_records: Mapped[List["SalaryRecord"]] = relationship(back_populates="employee", cascade="all, delete-orphan")

    @property
    def full_name(self) -> str:
        return f"{self.title or ''} {self.first_name} {self.last_name}".strip()

    def __repr__(self) -> str:
        return f"<Employee {self.employee_code} {self.full_name}>"


class Attendance(BaseModel):
    __tablename__ = 'attendance'
    __table_args__ = (UniqueConstraint('employee_id', 'attendance_date'),)

    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey('employees.id'), index=True, nullable=False)
    attendance_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    check_in_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    check_out_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    leave_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    employee: Mapped["Employee"] = relationship(back_populates="attendance_records")

    def __repr__(self) -> str:
        return f"<Attendance {self.employee_id} {self.attendance_date} {self.status}>"


class SalaryRecord(BaseModel):
    __tablename__ = 'salary_records'
    __table_args__ = (UniqueConstraint('employee_id', 'month', 'year'),)

    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey('employees.id'), index=True, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    basic_salary: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    allowances: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    deductions: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    net_salary: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    payment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    payment_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False)

    employee: Mapped["Employee"] = relationship(back_populates="salary_records")

    def __repr__(self) -> str:
        return f"<SalaryRecord {self.employee_id} {self.month}/{self.year}>"
