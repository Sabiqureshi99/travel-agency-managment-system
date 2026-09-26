"""
services/checkout_service.py
============================
Orchestrates cross-module transactions for Umrah Packages.
It handles creating the master Umrah booking, dispatching sub-services 
(Flights, Visa, Hotels), and generating a unified Invoice.
"""
from typing import Dict, Any, Optional
import uuid
from datetime import date
from sqlalchemy.orm import Session

from core.base_service import BaseService
from models.umrah import CustomUmrahBooking
from models.flight import FlightBooking
from models.visa import VisaApplication
from models.hotel import HotelBooking
from models.accounting import Invoice, InvoiceItem

class CheckoutService(BaseService):
    def process_umrah_booking(self, session: Session, booking_data: Dict[str, Any], current_user_id: str) -> CustomUmrahBooking:
        """
        Creates the entire Umrah package inside a single database transaction.
        If any step fails, the entire transaction is rolled back by the session context manager.
        """
        try:
            # 1. Create Master Umrah Booking
            umrah = CustomUmrahBooking(
                booking_number=f"UMR-{uuid.uuid4().hex[:6].upper()}",
                customer_id=booking_data['customer_id'],
                booking_date=date.today(),
                status='Confirmed'
            )
            session.add(umrah)
            session.flush() # To get the umrah.id

            invoice_items = []
            total_amount = 0.0

            # 2. Process Flights
            flight_data = booking_data.get('flights')
            if flight_data:
                flight = FlightBooking(
                    booking_number=f"FL-{uuid.uuid4().hex[:6].upper()}",
                    customer_id=booking_data['customer_id'],
                    umrah_booking_id=umrah.id,
                    flight_type='Return',
                    trip_type='International',
                    airline=flight_data.get('airline', 'Unknown'),
                    origin=flight_data.get('origin', 'KHI'),
                    destination=flight_data.get('destination', 'JED'),
                    departure_date=flight_data.get('departure_date', date.today()),
                    selling_price=flight_data.get('price', 0)
                )
                session.add(flight)
                
                total_amount += float(flight.selling_price)
                invoice_items.append(
                    InvoiceItem(
                        description=f"Flight Ticket - {flight.airline} ({flight.origin} to {flight.destination})",
                        quantity=flight_data.get('pax', 1),
                        unit_price=float(flight.selling_price),
                        total_price=float(flight.selling_price) * int(flight_data.get('pax', 1))
                    )
                )

            # 3. Process Visa
            visa_data = booking_data.get('visa')
            if visa_data:
                visa = VisaApplication(
                    application_number=f"VSA-{uuid.uuid4().hex[:6].upper()}",
                    customer_id=booking_data['customer_id'],
                    umrah_booking_id=umrah.id,
                    country="Saudi Arabia",
                    visa_type=visa_data.get('type', 'Umrah'),
                    application_date=date.today(),
                    total_cost=visa_data.get('price', 0)
                )
                session.add(visa)
                
                total_amount += float(visa.total_cost)
                invoice_items.append(
                    InvoiceItem(
                        description=f"Visa Processing - {visa.country} {visa.visa_type}",
                        quantity=visa_data.get('pax', 1),
                        unit_price=float(visa.total_cost),
                        total_price=float(visa.total_cost) * int(visa_data.get('pax', 1))
                    )
                )

            # 4. Process Hotels
            hotel_data = booking_data.get('hotel')
            if hotel_data:
                # Fallback to None or raise ValueError instead of violating FK constraint
                hotel_id = hotel_data.get('hotel_id')
                if not hotel_id:
                    raise ValueError("Hotel ID is required for a hotel booking.")
                
                hotel = HotelBooking(
                    booking_number=f"HTL-{uuid.uuid4().hex[:6].upper()}",
                    hotel_id=hotel_id,
                    customer_id=booking_data['customer_id'],
                    umrah_booking_id=umrah.id,
                    check_in_date=hotel_data.get('check_in_date', date.today()),
                    check_out_date=hotel_data.get('check_out_date', date.today()),
                    total_selling=hotel_data.get('price', 0)
                )
                session.add(hotel)
                
                total_amount += float(hotel.total_selling)
                invoice_items.append(
                    InvoiceItem(
                        description=f"Hotel Accommodation - {hotel_data.get('hotel_name', 'TBD')} ({hotel.nights} Nights)",
                        quantity=1,
                        unit_price=float(hotel.total_selling),
                        total_price=float(hotel.total_selling)
                    )
                )
                
            # Ziyarat & Transport
            transport_data = booking_data.get('transport')
            if transport_data:
                price = transport_data.get('price', 0)
                total_amount += float(price)
                invoice_items.append(
                    InvoiceItem(
                        description=f"Transport & Ziyarat - {transport_data.get('type', 'Standard')}",
                        quantity=1,
                        unit_price=float(price),
                        total_price=float(price)
                    )
                )

            # 5. Generate Invoice
            invoice = Invoice(
                invoice_number=f"INV-{uuid.uuid4().hex[:6].upper()}",
                customer_id=booking_data['customer_id'],
                issue_date=date.today(),
                reference_type='CustomUmrahBooking',
                reference_id=umrah.id,
                subtotal=total_amount,
                total_amount=total_amount,
                amount_remaining=total_amount,
                status="Unpaid"
            )
            session.add(invoice)
            session.flush()

            for item in invoice_items:
                item.invoice_id = invoice.id
                session.add(item)
                
            umrah.final_total_price = total_amount
            
            # Commit the transaction
            session.commit()
            return umrah
            
        except Exception as e:
            # Rollback to avoid dirty sessions
            session.rollback()
            raise e
