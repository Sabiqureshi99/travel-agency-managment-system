import re
from datetime import date, timedelta
from typing import Any

def validate_cnic(cnic: str) -> bool:
    """Pakistan CNIC: XXXXX-XXXXXXX-X (13 digits + 2 dashes)"""
    pattern = r"^\d{5}-\d{7}-\d{1}$"
    return bool(re.match(pattern, cnic))

def validate_passport(passport: str) -> bool:
    """alpha + numeric, 6-9 chars, uppercase first letter"""
    pattern = r"^[A-Z][a-zA-Z0-9]{5,8}$"
    return bool(re.match(pattern, passport))

def validate_phone_pk(phone: str) -> bool:
    """accepts +92XXXXXXXXXX, 03XXXXXXXXX, 3XXXXXXXXX"""
    pattern = r"^(?:\+92|03|3)\d{9}$"
    return bool(re.match(pattern, phone))

def validate_email(email: str) -> bool:
    """standard email regex"""
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return bool(re.match(pattern, email))

def validate_ntn(ntn: str) -> bool:
    """Pakistan NTN: 7 digits (XXXXXXX-X format)"""
    pattern = r"^\d{7}-\d{1}$"
    return bool(re.match(pattern, ntn))

def validate_date_range(start: date, end: date) -> bool:
    """Ensure start date is not after end date."""
    return start <= end

def validate_positive_amount(amount: Any) -> bool:
    """Ensure amount is a valid positive number."""
    try:
        val = float(amount)
        return val > 0
    except (ValueError, TypeError):
        return False

def validate_required_fields(data: dict, fields: list[str]) -> dict[str, str]:
    """returns {field: error_msg} for any missing or empty fields."""
    errors = {}
    for field in fields:
        val = data.get(field)
        if val is None or (isinstance(val, str) and not val.strip()):
            errors[field] = f"Field '{field}' is required."
    return errors

def validate_passport_expiry(expiry_date: date) -> tuple[bool, str]:
    """Passport should generally have at least 6 months validity."""
    if expiry_date < date.today():
        return False, "Passport is expired."
    if expiry_date < date.today() + timedelta(days=180):
        return False, "Passport expires in less than 6 months."
    return True, ""

def sanitize_string(s: str) -> str:
    """Removes leading/trailing whitespace and multiple internal spaces."""
    if not isinstance(s, str):
        return str(s)
    return " ".join(s.split())

def sanitize_phone(phone: str) -> str:
    """normalize to +92XXXXXXXXXX if Pakistani"""
    s_phone = "".join(filter(str.isdigit, phone))
    if s_phone.startswith("92") and len(s_phone) == 12:
        return "+" + s_phone
    elif s_phone.startswith("03") and len(s_phone) == 11:
        return "+92" + s_phone[1:]
    elif s_phone.startswith("3") and len(s_phone) == 10:
        return "+92" + s_phone
    return "+" + s_phone if not phone.startswith("+") else phone
