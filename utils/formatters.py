from datetime import date, datetime
import math

def format_currency(amount: float, currency: str = 'PKR', show_symbol: bool = True) -> str:
    """Format an amount as currency, e.g. 'Rs. 1,500.00'"""
    prefix = "Rs. " if currency == 'PKR' and show_symbol else (f"{currency} " if show_symbol else "")
    return f"{prefix}{amount:,.2f}"

def format_date(d: date | datetime | None, fmt: str = '%d-%b-%Y') -> str:
    """Format a date object to string."""
    if d is None:
        return ""
    return d.strftime(fmt)

def format_datetime(dt: datetime | None) -> str:
    """Format a datetime object to string."""
    if dt is None:
        return ""
    return dt.strftime('%d-%b-%Y %I:%M %p')

def format_cnic(cnic: str) -> str:
    """Ensures XXXXX-XXXXXXX-X format for CNIC."""
    digits = "".join(filter(str.isdigit, cnic))
    if len(digits) == 13:
        return f"{digits[:5]}-{digits[5:12]}-{digits[12]}"
    return cnic

def format_phone(phone: str) -> str:
    """Formats phone number by sanitizing it."""
    from utils.validators import sanitize_phone
    return sanitize_phone(phone)

def format_passport(passport: str) -> str:
    """Formats passport by trimming and converting to uppercase."""
    return passport.strip().upper()

def truncate(text: str, max_len: int = 50, suffix: str = '...') -> str:
    """Truncates text to a maximum length."""
    if len(text) <= max_len:
        return text
    return text[:max_len - len(suffix)] + suffix

def format_file_size(size_bytes: int) -> str:
    """Formats bytes to a human-readable size e.g., '1.5 MB'"""
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

def ordinal(n: int) -> str:
    """Returns ordinal string for an integer: '1st', '2nd', '3rd', etc."""
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    else:
        suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
    return f"{n}{suffix}"

def format_percentage(value: float, decimals: int = 1) -> str:
    """Formats value as a percentage, e.g., '12.5%'"""
    return f"{value:.{decimals}f}%"

def number_to_words_pkr(amount: float) -> str:
    """e.g. 'One Thousand Five Hundred Rupees Only'"""
    try:
        from num2words import num2words
        words = num2words(int(amount), lang='en_IN').title().replace(',', '')
        return f"{words} Rupees Only"
    except ImportError:
        # Fallback if num2words is not installed
        return f"{amount:,.2f} Rupees Only"
