import sys
import os
from pathlib import Path
from datetime import timedelta, date, datetime, timezone
import random

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env", override=False)

from utils.logger import setup_logging
setup_logging()

from faker import Faker
from config.database import get_session, init_database
from core.base_model import generate_uuid
from services.unified_booking_service import UnifiedBookingService

# Import all models
from models.customer import Customer
from models.vendor import Vendor
from models.flight import FlightBooking
from models.visa import VisaApplication
from models.hotel import Hotel
from models.transport import Vehicle
from models.accounting import ChartOfAccount, Receipt, Expense
from models.booking import Booking

fake = Faker()
Faker.seed(42)
random.seed(42)

NUM_VENDORS = 1200
NUM_CUSTOMERS = 1200
NUM_HOTELS = 1200
NUM_VEHICLES = 1200
NUM_BOOKINGS = 1200
NUM_FLIGHTS = 1200
NUM_VISAS = 1200
NUM_RECEIPTS = 1200
NUM_EXPENSES = 1200

def generate_vendors(session):
    print(f"Generating {NUM_VENDORS} vendors...")
    vendors = []
    types = ['Airline', 'Hotel', 'Transport', 'Visa Agent', 'Other']
    for i in range(NUM_VENDORS):
        vendor = Vendor()
        vendor.id = generate_uuid()
        vendor.vendor_code = f"VND-{fake.unique.random_number(digits=6, fix_len=True)}"
        vendor.company_name = fake.company()
        vendor.vendor_type = random.choice(types)
        vendor.contact_person = fake.name()
        vendor.phone = fake.phone_number()[:20]
        vendor.email = fake.company_email()
        vendor.city = fake.city()
        vendor.country = fake.country()
        vendor.opening_balance = 0
        vendor.status = 'Active'
        vendors.append(vendor)
    session.add_all(vendors)
    session.commit()
    return vendors

def generate_customers(session):
    print(f"Generating {NUM_CUSTOMERS} customers...")
    customers = []
    for i in range(NUM_CUSTOMERS):
        cust = Customer()
        cust.id = generate_uuid()
        cust.customer_code = f"CUST-{fake.unique.random_number(digits=6, fix_len=True)}"
        cust.first_name = fake.first_name()
        cust.last_name = fake.last_name()
        cust.phone_primary = fake.phone_number()[:20]
        cust.cnic = str(fake.random_number(digits=13, fix_len=True))
        cust.passport_number = fake.bothify(text='??#######').upper()
        cust.city = fake.city()
        cust.country = fake.country()
        cust.customer_type = random.choice(['Individual', 'Corporate'])
        customers.append(cust)
        if len(customers) >= 500:
            session.add_all(customers)
            customers = []
    if customers:
        session.add_all(customers)
    session.commit()
    
def generate_hotels(session, vendor_ids):
    print(f"Generating {NUM_HOTELS} hotels...")
    hotels = []
    for i in range(NUM_HOTELS):
        h = Hotel()
        h.id = generate_uuid()
        h.hotel_code = f"HTL-{fake.unique.random_number(digits=6, fix_len=True)}"
        h.hotel_name = fake.company() + " Hotel"
        h.city = fake.city()
        h.country = fake.country()
        h.star_rating = random.randint(1, 5)
        h.vendor_id = random.choice(vendor_ids) if vendor_ids else None
        hotels.append(h)
    session.add_all(hotels)
    session.commit()

def generate_vehicles(session):
    print(f"Generating {NUM_VEHICLES} vehicles...")
    vehicles = []
    types = ['Sedan', 'SUV', 'Bus', 'Van']
    for i in range(NUM_VEHICLES):
        v = Vehicle()
        v.id = generate_uuid()
        v.registration_number = fake.unique.license_plate()[:30]
        v.make = fake.company()
        v.model = fake.word().capitalize()
        v.year = int(fake.year())
        v.vehicle_type = random.choice(types)
        v.capacity = random.choice([4, 7, 12, 50])
        vehicles.append(v)
    session.add_all(vehicles)
    session.commit()

def generate_unified_bookings(session, customer_ids, hotel_ids, vehicle_ids, vendor_ids):
    print(f"Generating {NUM_BOOKINGS} unified bookings...")
    booking_service = UnifiedBookingService(session)
    for i in range(NUM_BOOKINGS):
        customer_id = random.choice(customer_ids)
        hotel_id = random.choice(hotel_ids)
        vehicle_id = random.choice(vehicle_ids)
        vendor_id = random.choice(vendor_ids)
        
        booking_data = {
            'cost_price': round(random.uniform(50000, 200000), 2),
            'selling_price': round(random.uniform(250000, 400000), 2)
        }
        
        pax_list = []
        num_pax = random.randint(1, 4)
        for j in range(num_pax):
            pax_list.append({
                'first_name': fake.first_name(),
                'last_name': fake.last_name(),
                'passport': fake.bothify(text='??#######').upper(),
                'cnic': str(fake.random_number(digits=13, fix_len=True)),
                'is_group_leader': (j == 0),
                'dob': fake.date_of_birth(minimum_age=1, maximum_age=80),
                'linked_customer_id': customer_id if j == 0 else None
            })
            
        check_in = fake.date_between(start_date='today', end_date='+30d')
        services = {
            'hotel': {
                'hotel_id': hotel_id,
                'vendor_id': vendor_id,
                'check_in_date': check_in,
                'check_out_date': check_in + timedelta(days=random.randint(2, 10)),
                'cost_price': round(random.uniform(10000, 50000), 2),
                'selling_price': round(random.uniform(60000, 100000), 2)
            },
            'transport': {
                'vehicle_id': vehicle_id,
                'vendor_id': vendor_id,
                'pickup_date': check_in,
                'pickup_time': "10:00",
                'pickup_location': fake.address()[:300],
                'dropoff_location': fake.address()[:300],
                'cost_price': round(random.uniform(5000, 15000), 2),
                'selling_price': round(random.uniform(20000, 30000), 2)
            }
        }
        
        try:
            booking_service.save_unified_booking(customer_id, booking_data, pax_list, services)
        except Exception as e:
            print(f"Skipping a booking due to error: {e}")
            session.rollback()
            continue
            
        if i % 100 == 0 and i > 0:
            print(f"  ... {i} bookings created")
            
def generate_flights(session, customer_ids, vendor_ids):
    print(f"Generating {NUM_FLIGHTS} standalone flight bookings...")
    flights = []
    for i in range(NUM_FLIGHTS):
        fb = FlightBooking()
        fb.id = generate_uuid()
        fb.booking_number = f"FB-{fake.unique.random_number(digits=6, fix_len=True)}"
        fb.customer_id = random.choice(customer_ids)
        fb.vendor_id = random.choice(vendor_ids)
        fb.flight_type = random.choice(['Domestic', 'International'])
        fb.trip_type = random.choice(['One Way', 'Round Trip'])
        fb.airline = fake.company() + " Airlines"
        fb.origin = fake.city()
        fb.destination = fake.city()
        fb.departure_date = fake.date_between(start_date='today', end_date='+60d')
        fb.selling_price = round(random.uniform(50000, 150000), 2)
        flights.append(fb)
        
        if len(flights) >= 500:
            session.add_all(flights)
            flights = []
    if flights:
        session.add_all(flights)
    session.commit()

def generate_visas(session, customer_ids, vendor_ids):
    print(f"Generating {NUM_VISAS} standalone visa applications...")
    visas = []
    for i in range(NUM_VISAS):
        v = VisaApplication()
        v.id = generate_uuid()
        v.application_number = f"VA-{fake.unique.random_number(digits=6, fix_len=True)}"
        v.customer_id = random.choice(customer_ids)
        v.vendor_id = random.choice(vendor_ids)
        v.country = fake.country()
        v.visa_type = random.choice(['Tourist', 'Business', 'Work', 'Student'])
        v.application_date = fake.date_between(start_date='-30d', end_date='today')
        v.sales_price = round(random.uniform(10000, 50000), 2)
        visas.append(v)
        
        if len(visas) >= 500:
            session.add_all(visas)
            visas = []
    if visas:
        session.add_all(visas)
    session.commit()
    
def generate_receipts(session, customer_ids, accounts):
    print(f"Generating {NUM_RECEIPTS} receipts...")
    receipts = []
    methods = ['Cash', 'Bank Transfer', 'Cheque', 'Card']
    bank_account_id = None
    cash_account_id = None
    for acc in accounts:
        if acc.account_code == '1121':
            bank_account_id = acc.id
        elif acc.account_code == '1110':
            cash_account_id = acc.id
            
    for i in range(NUM_RECEIPTS):
        r = Receipt()
        r.id = generate_uuid()
        r.receipt_number = f"RCT-{fake.unique.random_number(digits=6, fix_len=True)}"
        r.customer_id = random.choice(customer_ids)
        r.receipt_date = fake.date_between(start_date='-60d', end_date='today')
        r.amount = round(random.uniform(1000, 100000), 2)
        r.payment_method = random.choice(methods)
        r.bank_account_id = cash_account_id if r.payment_method == 'Cash' else bank_account_id
        receipts.append(r)
        
        if len(receipts) >= 500:
            session.add_all(receipts)
            receipts = []
    if receipts:
        session.add_all(receipts)
    session.commit()

def generate_expenses(session, accounts):
    print(f"Generating {NUM_EXPENSES} expenses...")
    expenses = []
    expense_account_ids = [acc.id for acc in accounts if acc.account_type == 'Expense' and acc.is_leaf]
    payment_account_ids = [acc.id for acc in accounts if acc.is_leaf and acc.account_type == 'Asset']
    
    if not expense_account_ids:
        print("No expense accounts found, skipping expenses.")
        return
        
    for i in range(NUM_EXPENSES):
        e = Expense()
        e.id = generate_uuid()
        e.expense_number = f"EXP-{fake.unique.random_number(digits=6, fix_len=True)}"
        e.account_id = random.choice(expense_account_ids)
        e.payment_account_id = random.choice(payment_account_ids) if payment_account_ids else None
        e.expense_date = fake.date_between(start_date='-60d', end_date='today')
        e.amount = round(random.uniform(500, 50000), 2)
        e.payment_method = random.choice(['Cash', 'Bank Transfer', 'Card'])
        e.description = fake.sentence()
        expenses.append(e)
        
        if len(expenses) >= 500:
            session.add_all(expenses)
            expenses = []
    if expenses:
        session.add_all(expenses)
    session.commit()

def main():
    print("Initializing Database connection...")
    init_database()
    
    with get_session() as session:
        # Load chart of accounts
        accounts = session.query(ChartOfAccount).all()
        if not accounts:
            print("Chart of Accounts is empty. Please run setup_initial_data.py first.")
            return

        generate_vendors(session)
        generate_customers(session)
        
        vendor_ids = [v.id for v in session.query(Vendor.id).all()]
        customer_ids = [c.id for c in session.query(Customer.id).all()]
        
        generate_hotels(session, vendor_ids)
        generate_vehicles(session)
        
        hotel_ids = [h.id for h in session.query(Hotel.id).all()]
        vehicle_ids = [v.id for v in session.query(Vehicle.id).all()]
        
        generate_unified_bookings(session, customer_ids, hotel_ids, vehicle_ids, vendor_ids)
        generate_flights(session, customer_ids, vendor_ids)
        generate_visas(session, customer_ids, vendor_ids)
        generate_receipts(session, customer_ids, accounts)
        generate_expenses(session, accounts)
        
    print("\n✅ Seed data generation complete! You can now launch TAMS to test.")

if __name__ == "__main__":
    main()
