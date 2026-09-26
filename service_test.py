import sys
import traceback
import os

# Load .env so DB_USE_SQLITE_FALLBACK etc. are read
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
except ImportError:
    pass
# Force SQLite fallback if Postgres not available
os.environ.setdefault('DB_USE_SQLITE_FALLBACK', 'true')

try:
    from services.customer_service import CustomerService
    from services.hotel_service import HotelService
    from services.umrah_service import UmrahService
    from services.hajj_service import HajjService
    from services.accounting_service import AccountingService
    from services.flight_service import FlightService
    from services.visa_service import VisaService
    from services.employee_service import EmployeeService

    tests = [
        ("CustomerService.search_customers", lambda: CustomerService().search_customers("", [])),
        ("HotelService.search_hotels", lambda: HotelService().search_hotels("")),
        ("HotelService.search_hotel_bookings", lambda: HotelService().search_hotel_bookings("")),
        ("UmrahService.search_packages", lambda: UmrahService().search_packages("")),
        ("UmrahService.search_bookings", lambda: UmrahService().search_bookings("")),
        ("HajjService.search_groups", lambda: HajjService().search_groups("")),
        ("AccountingService.search_invoices", lambda: AccountingService().search_invoices("")),
        ("AccountingService.search_expenses", lambda: AccountingService().search_expenses("")),
        ("FlightService.search_flights", lambda: FlightService().search_flights("")),
        ("VisaService.search_visas", lambda: VisaService().search_visas("")),
        ("EmployeeService.search_employees", lambda: EmployeeService().search_employees("")),
    ]

    all_passed = True
    for name, fn in tests:
        try:
            result = fn()
            if isinstance(result, dict):
                count = result.get("total", "?")
                print(f"  [PASS] {name} -> total={count}")
            elif isinstance(result, list):
                print(f"  [PASS] {name} -> {len(result)} records")
            else:
                print(f"  [PASS] {name} -> OK")
        except Exception as e:
            print(f"  [FAIL] {name} -> {e}")
            traceback.print_exc()
            all_passed = False

    print()
    if all_passed:
        print("ALL SERVICE TESTS PASSED")
    else:
        print("SOME TESTS FAILED - see above")
        sys.exit(1)

except ImportError as e:
    print(f"Import Error: {e}")
    traceback.print_exc()
    sys.exit(1)
