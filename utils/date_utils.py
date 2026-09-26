from datetime import date, datetime, timedelta
import calendar

def today() -> date:
    """Get the current date."""
    return date.today()

def now() -> datetime:
    """Get the current date and time."""
    return datetime.now()

def days_until(target_date: date) -> int:
    """Returns number of days until target_date (negative if in the past)."""
    return (target_date - today()).days

def days_since(past_date: date) -> int:
    """Returns number of days since past_date."""
    return (today() - past_date).days

def is_expired(expiry_date: date) -> bool:
    """Checks if the expiry_date is in the past."""
    return expiry_date < today()

def is_expiring_soon(expiry_date: date, days: int = 30) -> bool:
    """Checks if the expiry_date is approaching within the given days."""
    diff = (expiry_date - today()).days
    return 0 <= diff <= days

def fiscal_year_start(ref_date: date | None = None) -> date:
    """Pakistan fiscal year starts on July 1."""
    d = ref_date or today()
    if d.month >= 7:
        return date(d.year, 7, 1)
    else:
        return date(d.year - 1, 7, 1)

def fiscal_year_end(ref_date: date | None = None) -> date:
    """Pakistan fiscal year ends on June 30."""
    start = fiscal_year_start(ref_date)
    return date(start.year + 1, 6, 30)

def get_month_range(year: int, month: int) -> tuple[date, date]:
    """Returns the first and last day of the specified month."""
    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    return first_day, last_day

def get_year_range(year: int) -> tuple[date, date]:
    """Returns the first and last day of the specified year."""
    return date(year, 1, 1), date(year, 12, 31)

def format_duration(start: date, end: date) -> str:
    """Formats the duration in nights."""
    days = (end - start).days
    if days <= 0:
        return "Same day"
    elif days == 1:
        return "1 night"
    else:
        return f"{days} nights"

def parse_date(date_str: str) -> date | None:
    """Tries parsing a date string using multiple formats."""
    formats = ['%Y-%m-%d', '%d-%b-%Y', '%d/%m/%Y', '%d-%m-%Y', '%m/%d/%Y']
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            pass
    return None

def get_age(dob: date) -> int:
    """Calculates age in years from Date of Birth."""
    t = today()
    return t.year - dob.year - ((t.month, t.day) < (dob.month, dob.day))

def months_between(d1: date, d2: date) -> int:
    """Calculates the absolute number of months between two dates."""
    return abs((d1.year - d2.year) * 12 + d1.month - d2.month)
