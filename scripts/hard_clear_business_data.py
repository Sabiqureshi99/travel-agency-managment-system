# scripts/hard_clear_business_data.py
from sqlalchemy import text
from core.database import SessionLocal  # adjust import if different

TABLES_IN_DELETE_ORDER = [
    # accounting/finance child tables
    "journal_lines",
    "payment_transactions",
    "invoice_items",
    "receipts",
    "expenses",
    "vendor_payments",
    "withdrawals",
    "internal_transfers",
    "vendor_ledgers",

    # booking-related transactional tables (adjust to your schema)
    "flight_bookings",
    "visa_applications",
    "hotel_bookings",
    "transport_bookings",
    "tour_bookings",
    "hajj_bookings",
    "umrah_bookings",

    # parent financial tables
    "invoices",
    "journal_entries",

    # vendor & customer business masters
    "vendors",
    "customers",
]

def main():
    session = SessionLocal()
    try:
        # SQLite-safe FK handling; harmless on engines that ignore it
        session.execute(text("PRAGMA foreign_keys = OFF"))

        for table in TABLES_IN_DELETE_ORDER:
            session.execute(text(f"DELETE FROM {table}"))
            print(f"Cleared: {table}")

        session.commit()
        print("SUCCESS: All requested business data hard-deleted.")
    except Exception as exc:
        session.rollback()
        print(f"FAILED: {exc}")
        raise
    finally:
        try:
            session.execute(text("PRAGMA foreign_keys = ON"))
            session.commit()
        except Exception:
            session.rollback()
        session.close()

if __name__ == "__main__":
    main()