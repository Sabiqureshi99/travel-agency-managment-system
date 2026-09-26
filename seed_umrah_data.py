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
from config.database import get_session
from services.umrah_checkout_service import UmrahCheckoutService
from models.customer import Customer

fake = Faker()
Faker.seed(123)
random.seed(123)

NUM_UMRAH_BOOKINGS = 1200

def generate_umrah_bookings():
    print(f"Generating {NUM_UMRAH_BOOKINGS} Umrah bookings...")
    with get_session() as session:
        customer_ids = [c.id for c in session.query(Customer).all()]
        if not customer_ids:
            print("No customers found. Run seed_fake_data.py first.")
            return

        checkout_service = UmrahCheckoutService()
        
        for i in range(NUM_UMRAH_BOOKINGS):
            customer_id = random.choice(customer_ids)
            
            pax_list = []
            num_pax = random.randint(1, 4)
            for j in range(num_pax):
                pax_list.append({
                    'full_name': fake.name(),
                    'passport_number': fake.bothify(text='??#######').upper(),
                    'group_no': f"GRP-{i}",
                    'gender': random.choice(['Male', 'Female'])
                })
            
            data_payload = {
                'base_package_price': round(random.uniform(50000, 100000), 2),
                'base_purchase_cost': round(random.uniform(40000, 80000), 2),
                'total_pilgrims': num_pax,
                'passengers': pax_list,
                'flights': [
                    {
                        'leg_type': 'Outbound',
                        'airline': fake.company() + ' Airlines',
                        'flight_number': fake.bothify(text='??-###').upper(),
                        'origin': fake.city(),
                        'destination': 'JED',
                        'departure_date': fake.date_between(start_date='today', end_date='+30d'),
                        'pax': num_pax,
                        'purchase_price': round(random.uniform(30000, 60000), 2),
                        'sales_price': round(random.uniform(40000, 80000), 2)
                    }
                ],
                'visa': {
                    'type': 'Umrah e-Visa',
                    'pax': num_pax,
                    'purchase_price': 15000,
                    'sales_price': 20000
                },
                'hotels': [
                    {
                        'city': 'Makkah',
                        'hotel_name': fake.company() + ' Hotel',
                        'check_in_date': fake.date_between(start_date='today', end_date='+30d'),
                        'check_out_date': fake.date_between(start_date='+30d', end_date='+40d'),
                        'room_type': 'DOUBLE',
                        'rooms_count': 1,
                        'purchase_price': 20000,
                        'sales_price': 30000
                    }
                ],
                'transport': [
                    {
                        'type': 'BUS',
                        'service_route': 'JED-MAK',
                        'pickup_date': fake.date_between(start_date='today', end_date='+30d').strftime('%Y-%m-%d'),
                        'purchase_price': 5000,
                        'sales_price': 8000
                    }
                ]
            }
            
            try:
                checkout_service.create_unified_booking(session, customer_id, data_payload, "admin")
            except Exception as e:
                print(f"Skipping a booking due to error: {e}")
                session.rollback()
                continue
                
            if i % 100 == 0 and i > 0:
                print(f"  ... {i} bookings created")
                
        print("\n Umrah seed data generation complete!")

if __name__ == "__main__":
    generate_umrah_bookings()
