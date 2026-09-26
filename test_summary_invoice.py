import os
import sys
from dotenv import load_dotenv

# Add the project root to sys.path so imports work
sys.path.insert(0, os.path.abspath('.'))
load_dotenv()
os.environ['DATABASE_URL'] = 'sqlite:///data/hamza_travels.db'
os.environ['DATABASE_URL'] = 'sqlite:///data/hamza_travels.db'

from config.database import get_session
from models.accounting import Invoice
from models.umrah import CustomUmrahBooking
from services.invoice_generator import InvoiceGenerator

def test_summary_invoice():
    try:
        with get_session() as session:
            # find an invoice
            invoice = session.query(Invoice).first()
            if not invoice:
                print("No invoice found.")
                return
            
            umrah = session.query(CustomUmrahBooking).filter_by(id=invoice.reference_id).first()
            pkg_name = "Test Pkg"
            if umrah and umrah.template:
                pkg_name = umrah.template.name
                
            path = "test_summary_invoice.pdf"
            InvoiceGenerator.generate_invoice_pdf(invoice, path, is_package_summary=True, package_name=pkg_name)
            print(f"Success! Saved to {path}")
            
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_summary_invoice()
