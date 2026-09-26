import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Ensure paths are correct depending on where the script is executed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.booking import Booking
from models.vendor import VendorLedger
from models.accounting import Expense

DATABASE_URL = "sqlite:///data/hamza_travels.db" # Update if your connection string differs

def run_migration():
    # Use absolute path for DB if needed, but assuming run from root
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'hamza_travels.db'))
    engine = create_engine(f"sqlite:///{db_path}")
    
    with engine.connect() as conn:
        print("Migrating schema...")
        # 1. Add payment_method to bookings
        try:
            conn.execute(text("ALTER TABLE bookings ADD COLUMN payment_method VARCHAR(50)"))
        except Exception as e:
            print(f"Column payment_method might already exist on bookings: {e}")
            
        # 2. Add payment_source to vendor_ledgers
        try:
            conn.execute(text("ALTER TABLE vendor_ledgers ADD COLUMN payment_source VARCHAR(50)"))
        except Exception as e:
            print(f"Column payment_source might already exist on vendor_ledgers: {e}")
            
        # 3. Add payment_source to expenses
        try:
            conn.execute(text("ALTER TABLE expenses ADD COLUMN payment_source VARCHAR(50)"))
        except Exception as e:
            print(f"Column payment_source might already exist on expenses: {e}")

        conn.commit()
    
    # Data Sanitization
    Session = sessionmaker(bind=engine)
    with Session() as session:
        print("Sanitizing historical data...")
        
        # 1. Update Booking payment_method to 'Cash'
        session.query(Booking).filter(
            Booking.payment_method.is_(None)
        ).update({"payment_method": "Cash"}, synchronize_session=False)
        
        # 2. Update VendorLedger payment_source to 'Cash Drawer'
        session.query(VendorLedger).filter(
            VendorLedger.payment_source.is_(None)
        ).update({"payment_source": "Cash Drawer"}, synchronize_session=False)
        
        # 3. Update Expense payment_source to 'Cash Drawer'
        session.query(Expense).filter(
            Expense.payment_source.is_(None)
        ).update({"payment_source": "Cash Drawer"}, synchronize_session=False)
        
        session.commit()
        print("Migration and sanitization complete.")

if __name__ == "__main__":
    run_migration()
