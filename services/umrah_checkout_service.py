"""
services/umrah_checkout_service.py
==================================
Advanced orchestrator for Unified Umrah Bookings.
Supports robust create and update logic with diffing to manage cascading child records
(Flights, Visas, Hotels) and Invoice recalculations.
"""
import uuid
from typing import Dict, Any, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import select

from core.base_service import BaseService
from models.umrah import CustomUmrahBooking
from models.flight import FlightBooking
from models.visa import VisaApplication
from models.hotel import HotelBooking
from models.accounting import Invoice, InvoiceItem
from models.booking import Booking

class UmrahCheckoutService(BaseService):
    def create_unified_booking(self, session: Session, customer_id: str, data_payload: Dict[str, Any], user_id: str) -> CustomUmrahBooking:
        """Creates a new unified Umrah booking with cascading services and invoice."""
        try:
            # 1. Master Booking
            umrah_id = str(uuid.uuid4())
            umrah = CustomUmrahBooking(
                id=umrah_id,
                booking_number=f"UMR-{uuid.uuid4().hex[:6].upper()}",
                customer_id=customer_id,
                booking_date=date.today(),
                status='Confirmed',
                template_id=data_payload.get('template_id'),
                base_package_price=data_payload.get('base_package_price', 0),
                base_purchase_cost=data_payload.get('base_purchase_cost', 0),
                base_profit=data_payload.get('base_profit', 0),
                total_pilgrims=data_payload.get('total_pilgrims', 1),
                transport_details=data_payload.get('transport', [])
            )
            session.add(umrah)
            session.flush()

            total_amount = 0.0
            total_purchase_cost = 0.0
            invoice_items = []

            # 1.1 Passengers
            from models.umrah import UmrahPilgrim
            pax_data_list = data_payload.get('passengers', [])
            for pax_data in pax_data_list:
                if not pax_data.get('full_name') or not pax_data.get('passport_number'):
                    raise ValueError("Passenger Full Name and Passport Number are required.")

                pilgrim = UmrahPilgrim(
                    booking_id=umrah.id,
                    full_name=pax_data.get('full_name'),
                    passport_number=pax_data.get('passport_number'),
                    group_no=pax_data.get('group_no', ''),
                    gender=pax_data.get('gender', 'Not Specified'),
                    pax_type=pax_data.get('pax_type', 'Adult'),   # Phase 3
                )
                session.add(pilgrim)


            # 1.5 Add Base Package to invoice — categorical tier breakdown (Phase 4)
            _tier_cfg = [
                ("Adult",  "adult_count",  "adult_cost_price",  "adult_selling_price"),
                ("Child",  "child_count",  "child_cost_price",  "child_selling_price"),
                ("Infant", "infant_count", "infant_cost_price", "infant_selling_price"),
            ]
            for tier_label, qty_key, cost_key, sell_key in _tier_cfg:
                qty  = int(data_payload.get(qty_key, 0) or 0)
                cost = float(data_payload.get(cost_key, 0.0) or 0.0)
                sell = float(data_payload.get(sell_key, 0.0) or 0.0)
                if qty > 0:
                    subtotal_sell = qty * sell
                    subtotal_cost = qty * cost
                    total_amount       += subtotal_sell
                    total_purchase_cost += subtotal_cost
                    invoice_items.append(InvoiceItem(
                        description=f"Umrah Package — {tier_label} (x{qty})",
                        quantity=qty,
                        unit_price=sell,
                        total_price=subtotal_sell,
                    ))

            # 2. Flights (List)
            flight_data_list = data_payload.get('flights', [])
            for flight_data in flight_data_list:
                if not flight_data.get('airline') or not flight_data.get('origin') or not flight_data.get('destination'):
                    raise ValueError("Flight Airline, Origin, and Destination are required.")
                
                flight = FlightBooking(
                    booking_number=f"FL-{uuid.uuid4().hex[:6].upper()}",
                    customer_id=customer_id,
                    umrah_booking_id=umrah.id,
                    flight_type='Return',
                    trip_type='International',
                    leg_type=flight_data.get('leg_type', 'Outbound'),
                    airline=flight_data.get('airline'),
                    flight_number=flight_data.get('flight_number', None),
                    origin=flight_data.get('origin'),
                    destination=flight_data.get('destination'),
                    departure_time=flight_data.get('departure_time', None),
                    arrival_time=flight_data.get('arrival_time', None),
                    departure_date=flight_data.get('departure_date', date.today()),
                    selling_price=flight_data.get('sales_price', 0),
                    purchase_price=flight_data.get('purchase_price', 0),
                    sales_price=flight_data.get('sales_price', 0),
                    profit=flight_data.get('profit', 0),
                    pnr=flight_data.get('pnr', None)
                )
                session.add(flight)
                session.flush() # ensure flight.id is available
                
                from models.flight import FlightPassenger
                pax = int(flight_data.get('pax', 1))
                if pax_data_list and pax <= len(pax_data_list):
                    for i in range(pax):
                        fpax = FlightPassenger(
                            id=str(uuid.uuid4()),
                            booking_id=flight.id,
                            first_name=pax_data_list[i].get('full_name', '').split(' ')[0],
                            last_name=" ".join(pax_data_list[i].get('full_name', '').split(' ')[1:]),
                            passport_number=pax_data_list[i].get('passport_number', '')
                        )
                        session.add(fpax)
                else:
                    for i in range(pax):
                        fpax = FlightPassenger(
                            id=str(uuid.uuid4()),
                            booking_id=flight.id,
                            first_name="Passenger",
                            last_name=str(i+1),
                        )
                        session.add(fpax)
                price = float(flight.selling_price)
                pax = int(flight_data.get('pax', 1))
                total_amount += price * pax
                total_purchase_cost += float(flight.purchase_price) * pax
                invoice_items.append(InvoiceItem(
                    description=f"Flight [{flight.leg_type}] - {flight.airline} ({flight.origin}-{flight.destination})",
                    quantity=pax, unit_price=price, total_price=price * pax
                ))

            # 3. Visa (Single for now, could be list if needed)
            visa_data = data_payload.get('visa')
            if visa_data:
                visa = VisaApplication(
                    application_number=f"VSA-{uuid.uuid4().hex[:6].upper()}",
                    customer_id=customer_id,
                    umrah_booking_id=umrah.id,
                    country="Saudi Arabia",
                    visa_type=visa_data.get('type', 'Umrah e-Visa'),
                    application_date=date.today(),
                    status='Submitted',
                    purchase_price=visa_data.get('purchase_price', 0),
                    sales_price=visa_data.get('sales_price', 0),
                    profit=visa_data.get('profit', 0),
                    total_cost=visa_data.get('sales_price', 0),
                    notes="Auto-generated from Unified Booking"
                )
                session.add(visa)
                session.flush() # ensure visa.id is available
                
                from models.visa import VisaApplicant
                for pax in pax_data_list:
                    v_app = VisaApplicant(
                        visa_application_id=visa.id,
                        full_name=pax.get('full_name'),
                        passport_number=pax.get('passport_number'),
                        gender=pax.get('gender')
                    )
                    session.add(v_app)
                    
                price = float(visa.total_cost)
                pax = int(visa_data.get('pax', 1))
                total_amount += price * pax
                total_purchase_cost += float(visa.purchase_price) * pax
                invoice_items.append(InvoiceItem(
                    description=f"Visa - {visa.country} {visa.visa_type}",
                    quantity=pax, unit_price=price, total_price=price * pax
                ))

            # 4. Hotels (List)
            hotel_data_list = data_payload.get('hotels', [])
            total_nights_calc = 0
            room_types = set()
            
            for hotel_data in hotel_data_list:
                cin = hotel_data.get('check_in_date', date.today())
                cout = hotel_data.get('check_out_date', date.today())
                if isinstance(cin, str):
                    try: cin = date.fromisoformat(cin)
                    except: cin = date.today()
                if isinstance(cout, str):
                    try: cout = date.fromisoformat(cout)
                    except: cout = date.today()
                
                nights = (cout - cin).days
                if nights > 0:
                    total_nights_calc += nights
                    
                rt = hotel_data.get('room_type', 'DOUBLE')
                if rt:
                    room_types.add(str(rt))
                h_name = hotel_data.get('hotel_name', 'Unknown Hotel')
                if not h_name.strip(): h_name = 'Unknown Hotel'
                h_city = hotel_data.get('city', 'Unknown')
                
                from models.hotel import Hotel
                hotel_record = session.query(Hotel).filter(Hotel.hotel_name == h_name, Hotel.city == h_city).first()
                if not hotel_record:
                    hotel_record = Hotel(
                        hotel_code=f"HT-{uuid.uuid4().hex[:6].upper()}",
                        hotel_name=h_name,
                        city=h_city,
                        country="Saudi Arabia" if h_city in ["Makkah", "Medinah", "Jeddah", "Taif"] else "Unknown"
                    )
                    session.add(hotel_record)
                    session.flush()
                
                hotel = HotelBooking(
                    booking_number=f"HTL-{uuid.uuid4().hex[:6].upper()}",
                    hotel_id=hotel_record.id,
                    customer_id=customer_id,
                    umrah_booking_id=umrah.id,
                    city=h_city,
                    check_in_date=cin,
                    check_out_date=cout,
                    total_selling=hotel_data.get('sales_price', 0),
                    notes=h_name,
                    hn_number=hotel_data.get('hn_number', None),
                    reservation_name=hotel_data.get('reservation_name', None),
                    hotel_name_override=hotel_data.get('hotel_name', None),
                    room_type=hotel_data.get('room_type', 'DOUBLE'),
                    num_rooms=int(hotel_data.get('rooms_count', 1)),
                    purchase_price=hotel_data.get('purchase_price', 0),
                    sales_price=hotel_data.get('sales_price', 0),
                    profit=hotel_data.get('profit', 0)
                )
                session.add(hotel)
                price = float(hotel.total_selling)
                total_amount += price
                total_purchase_cost += float(hotel.purchase_price)
                invoice_items.append(InvoiceItem(
                    description=f"Hotel [{hotel.city}] - {hotel.notes}",
                    quantity=1, unit_price=price, total_price=price
                ))
            
            # Apply calculated nights and room types to master record
            if total_nights_calc > 0:
                umrah.total_nights = total_nights_calc
            if room_types:
                umrah.room_type = "/".join(room_types)
                
            # Transport
            transport_data_list = data_payload.get('transport', [])
            for transport_data in transport_data_list:
                price = float(transport_data.get('sales_price', 0))
                total_amount += price
                total_purchase_cost += float(transport_data.get('purchase_price', 0))
                invoice_items.append(InvoiceItem(
                    description=f"Transport - {transport_data.get('type', 'Standard')}",
                    quantity=1, unit_price=price, total_price=price
                ))
                
                from models.transport import TransportBooking
                pickup = transport_data.get('pickup_date', date.today())
                if isinstance(pickup, str):
                    try:
                        from datetime import datetime
                        pickup = datetime.strptime(pickup, '%d/%m/%Y').date()
                    except:
                        pickup = date.today()
                        
                tb = TransportBooking(
                    booking_number=f"TR-{uuid.uuid4().hex[:6].upper()}",
                    customer_id=customer_id,
                    booking_date=date.today(),
                    pickup_location=transport_data.get('service_route', 'Umrah Route'),
                    dropoff_location="Various",
                    pickup_date=pickup,
                    pickup_time="10:00 AM",
                    total_amount=price,
                    purchase_price=transport_data.get('purchase_price', 0),
                    sales_price=price,
                    profit=transport_data.get('profit', 0),
                    status="Confirmed",
                    notes="Auto-generated from Unified Booking",
                    vehicle_type_override=transport_data.get('type'),
                    tn_number=transport_data.get('tn_number'),
                    booking_ref=transport_data.get('booking_ref'),
                    contact_person=transport_data.get('contact_person')
                )
                session.add(tb)

            umrah.final_total_price = total_amount

            # 5. Invoice
            invoice = Invoice(
                invoice_number=f"INV-{uuid.uuid4().hex[:6].upper()}",
                customer_id=customer_id,
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

            # 6. Centralized Booking Record — categorical pricing (Phase 1/3)
            central_booking = Booking(
                booking_type='Umrah_Package',
                customer_id=customer_id,
                package_id=umrah.id,
                # Categorical base-package pricing
                adult_count=data_payload.get('adult_count', 0),
                adult_cost_price=data_payload.get('adult_cost_price', 0.0),
                adult_selling_price=data_payload.get('adult_selling_price', 0.0),
                child_count=data_payload.get('child_count', 0),
                child_cost_price=data_payload.get('child_cost_price', 0.0),
                child_selling_price=data_payload.get('child_selling_price', 0.0),
                infant_count=data_payload.get('infant_count', 0),
                infant_cost_price=data_payload.get('infant_cost_price', 0.0),
                infant_selling_price=data_payload.get('infant_selling_price', 0.0),
                payment_method=data_payload.get('payment_method', 'Cash'),
            )
            session.add(central_booking)

                
            session.commit()
            return umrah
        except Exception as e:
            session.rollback()
            raise e

    def update_unified_booking(self, session: Session, booking_id: str, new_data_payload: Dict[str, Any], user_id: str) -> CustomUmrahBooking:
        """Diffs payload against existing booking, updates children, and recalculates invoice."""
        try:
            umrah = session.get(CustomUmrahBooking, booking_id)
            if not umrah:
                raise ValueError("Umrah booking not found")
            
            umrah.transport_details = new_data_payload.get('transport', [])
            umrah.base_package_price = new_data_payload.get('base_package_price', umrah.base_package_price)
            umrah.base_purchase_cost = new_data_payload.get('base_purchase_cost', umrah.base_purchase_cost)
            umrah.base_profit = new_data_payload.get('base_profit', umrah.base_profit)
            umrah.total_pilgrims = new_data_payload.get('total_pilgrims', umrah.total_pilgrims)
            
            # Diff Passengers
            from models.umrah import UmrahPilgrim
            pax_data_list = new_data_payload.get('passengers', [])
            existing_pax = list(umrah.pilgrims)
            for i in range(max(len(pax_data_list), len(existing_pax))):
                if i < len(pax_data_list) and i < len(existing_pax):
                    p_data = pax_data_list[i]
                    p_obj = existing_pax[i]
                    p_obj.full_name = p_data.get('full_name', p_obj.full_name)
                    p_obj.passport_number = p_data.get('passport_number', p_obj.passport_number)
                    p_obj.group_no = p_data.get('group_no', p_obj.group_no)
                    p_obj.pax_type = p_data.get('pax_type', getattr(p_obj, 'pax_type', 'Adult'))   # Phase 3
                elif i < len(pax_data_list):
                    p_data = pax_data_list[i]
                    if not p_data.get('full_name') or not p_data.get('passport_number'):
                        raise ValueError("Passenger Full Name and Passport Number are required.")
                    pilgrim = UmrahPilgrim(
                        booking_id=umrah.id,
                        full_name=p_data.get('full_name'),
                        passport_number=p_data.get('passport_number'),
                        group_no=p_data.get('group_no', ''),
                        gender=p_data.get('gender', 'Not Specified'),
                        pax_type=p_data.get('pax_type', 'Adult'),   # Phase 3
                    )
                    session.add(pilgrim)
                else:
                    session.delete(existing_pax[i])

            
            total_amount = 0.0
            new_invoice_items = []
            

            # Base Package — categorical tier breakdown (Phase 4)
            _tier_cfg = [
                ("Adult",  "adult_count",  "adult_selling_price"),
                ("Child",  "child_count",  "child_selling_price"),
                ("Infant", "infant_count", "infant_selling_price"),
            ]
            for tier_label, qty_key, sell_key in _tier_cfg:
                qty  = int(new_data_payload.get(qty_key, 0) or 0)
                sell = float(new_data_payload.get(sell_key, 0.0) or 0.0)
                if qty > 0:
                    subtotal_sell = qty * sell
                    total_amount += subtotal_sell
                    new_invoice_items.append(InvoiceItem(
                        description=f"Umrah Package — {tier_label} (x{qty})",
                        quantity=qty,
                        unit_price=sell,
                        total_price=subtotal_sell,
                    ))


            # 1. Diff Flights (List mapping by index)
            flight_data_list = new_data_payload.get('flights', [])
            existing_flights = list(umrah.flights)
            
            for i in range(max(len(flight_data_list), len(existing_flights))):
                if i < len(flight_data_list) and i < len(existing_flights):
                    # Update existing
                    f_data = flight_data_list[i]
                    f_obj = existing_flights[i]
                    
                    f_obj.leg_type = f_data.get('leg_type', f_obj.leg_type)
                    f_obj.airline = f_data.get('airline', f_obj.airline)
                    f_obj.flight_number = f_data.get('flight_number', f_obj.flight_number)
                    f_obj.origin = f_data.get('origin', f_obj.origin)
                    f_obj.destination = f_data.get('destination', f_obj.destination)
                    f_obj.departure_time = f_data.get('departure_time', f_obj.departure_time)
                    f_obj.arrival_time = f_data.get('arrival_time', f_obj.arrival_time)
                    f_obj.pnr = f_data.get('pnr', f_obj.pnr)
                    f_obj.selling_price = float(f_data.get('sales_price', 0))
                    f_obj.purchase_price = float(f_data.get('purchase_price', 0))
                    f_obj.sales_price = float(f_data.get('sales_price', 0))
                    f_obj.profit = float(f_data.get('profit', 0))
                    
                    pax = int(f_data.get('pax', 1))
                    price = float(f_obj.selling_price)
                    total_amount += price * pax
                    if pax_data_list and pax <= len(pax_data_list):
                        for i in range(pax):
                            new_invoice_items.append(InvoiceItem(
                                description=f"Flight [{f_obj.leg_type}] - {f_obj.airline} ({f_obj.origin}-{f_obj.destination})",
                                quantity=1, unit_price=price, total_price=price,
                                passenger_name=pax_data_list[i].get('full_name'),
                                passport_number=pax_data_list[i].get('passport_number')
                            ))
                    else:
                        new_invoice_items.append(InvoiceItem(
                            description=f"Flight [{f_obj.leg_type}] - {f_obj.airline} ({f_obj.origin}-{f_obj.destination})",
                            quantity=pax, unit_price=price, total_price=price * pax
                        ))
                    
                elif i < len(flight_data_list):
                    # Add new
                    if not f_data.get('airline') or not f_data.get('origin') or not f_data.get('destination'):
                        raise ValueError("Flight Airline, Origin, and Destination are required.")
                    flight = FlightBooking(
                        booking_number=f"FL-{uuid.uuid4().hex[:6].upper()}",
                        customer_id=umrah.customer_id, umrah_booking_id=umrah.id,
                        flight_type='Return', trip_type='International',
                        leg_type=f_data.get('leg_type', 'Outbound'),
                        airline=f_data.get('airline'),
                        flight_number=f_data.get('flight_number', None),
                        origin=f_data.get('origin'), destination=f_data.get('destination'),
                        departure_time=f_data.get('departure_time', None),
                        arrival_time=f_data.get('arrival_time', None),
                        departure_date=f_data.get('departure_date', date.today()),
                        selling_price=float(f_data.get('sales_price', 0)),
                        purchase_price=float(f_data.get('purchase_price', 0)),
                        sales_price=float(f_data.get('sales_price', 0)),
                        profit=float(f_data.get('profit', 0)),
                        pnr=f_data.get('pnr', None)
                    )
                    session.add(flight)
                    session.flush() # ensure flight.id is available
                    
                    from models.flight import FlightPassenger
                    pax = int(f_data.get('pax', 1))
                    if pax_data_list and pax <= len(pax_data_list):
                        for j in range(pax):
                            fpax = FlightPassenger(
                                id=str(uuid.uuid4()),
                                booking_id=flight.id,
                                first_name=pax_data_list[j].get('full_name', '').split(' ')[0],
                                last_name=" ".join(pax_data_list[j].get('full_name', '').split(' ')[1:]),
                                passport_number=pax_data_list[j].get('passport_number', '')
                            )
                            session.add(fpax)
                    else:
                        for j in range(pax):
                            fpax = FlightPassenger(
                                id=str(uuid.uuid4()),
                                booking_id=flight.id,
                                first_name="Passenger",
                                last_name=str(j+1),
                            )
                            session.add(fpax)
                    
                    pax = int(f_data.get('pax', 1))
                    price = float(flight.selling_price)
                    total_amount += price * pax
                    new_invoice_items.append(InvoiceItem(
                        description=f"Flight [{flight.leg_type}] - {flight.airline} ({flight.origin}-{flight.destination})",
                        quantity=pax, unit_price=price, total_price=price * pax
                    ))
                    
                else:
                    # Remove left over
                    session.delete(existing_flights[i])

            # 2. Diff Visa
            visa_data = new_data_payload.get('visa')
            existing_visa = next((v for v in umrah.visas), None)
            
            if visa_data:
                pax = int(visa_data.get('pax', 1))
                price = float(visa_data.get('sales_price', 0))
                
                if existing_visa:
                    existing_visa.visa_type = visa_data.get('type', existing_visa.visa_type)
                    existing_visa.total_cost = price
                    existing_visa.purchase_price = float(visa_data.get('purchase_price', 0))
                    existing_visa.sales_price = price
                    existing_visa.profit = float(visa_data.get('profit', 0))
                else:
                    visa = VisaApplication(
                        application_number=f"VSA-{uuid.uuid4().hex[:6].upper()}",
                        customer_id=umrah.customer_id, umrah_booking_id=umrah.id,
                        country="Saudi Arabia", visa_type=visa_data.get('type', 'Umrah e-Visa'),
                        application_date=date.today(), total_cost=price,
                        status='Submitted',
                        purchase_price=float(visa_data.get('purchase_price', 0)),
                        sales_price=price,
                        profit=float(visa_data.get('profit', 0)),
                        notes="Auto-generated from Unified Booking"
                    )
                    session.add(visa)
                    session.flush()
                    
                    from models.visa import VisaApplicant
                    for pax in pax_data_list:
                        v_app = VisaApplicant(
                            visa_application_id=visa.id,
                            full_name=pax.get('full_name'),
                            passport_number=pax.get('passport_number'),
                            gender=pax.get('gender')
                        )
                        session.add(v_app)
                    
                total_amount += price * pax
                v_type = visa_data.get('type', existing_visa.visa_type if existing_visa else 'Umrah')
                new_invoice_items.append(InvoiceItem(
                    description=f"Visa - Saudi Arabia {v_type}",
                    quantity=pax, unit_price=price, total_price=price * pax
                ))
            elif existing_visa:
                session.delete(existing_visa)

            # 3. Diff Hotels (List mapping by index)
            hotel_data_list = new_data_payload.get('hotels', [])
            existing_hotels = list(umrah.hotels)
            total_nights_calc = 0
            
            for i in range(max(len(hotel_data_list), len(existing_hotels))):
                if i < len(hotel_data_list) and i < len(existing_hotels):
                    # Update existing
                    h_data = hotel_data_list[i]
                    h_obj = existing_hotels[i]
                    
                    h_obj.city = h_data.get('city', h_obj.city)
                    h_obj.notes = h_data.get('hotel_name', h_obj.notes)
                    h_obj.hotel_name_override = h_data.get('hotel_name', h_obj.hotel_name_override)
                    h_obj.hn_number = h_data.get('hn_number', h_obj.hn_number)
                    h_obj.reservation_name = h_data.get('reservation_name', h_obj.reservation_name)
                    h_obj.room_type = h_data.get('room_type', h_obj.room_type)
                    h_obj.num_rooms = int(h_data.get('rooms_count', h_obj.num_rooms or 1))
                    h_obj.total_selling = float(h_data.get('sales_price', 0))
                    h_obj.purchase_price = float(h_data.get('purchase_price', 0))
                    h_obj.sales_price = float(h_data.get('sales_price', 0))
                    h_obj.profit = float(h_data.get('profit', 0))
                    
                    h_obj.check_in_date = h_data.get('check_in_date', h_obj.check_in_date)
                    h_obj.check_out_date = h_data.get('check_out_date', h_obj.check_out_date)
                    
                    cin = h_obj.check_in_date
                    cout = h_obj.check_out_date
                    if isinstance(cin, str):
                        try: cin = date.fromisoformat(cin)
                        except: cin = date.today()
                    if isinstance(cout, str):
                        try: cout = date.fromisoformat(cout)
                        except: cout = date.today()
                    nights = (cout - cin).days if cin and cout else 0
                    if nights > 0:
                        total_nights_calc += nights
                    
                    price = float(h_obj.total_selling)
                    total_amount += price
                    new_invoice_items.append(InvoiceItem(
                        description=f"Hotel [{h_obj.city}] - {h_obj.notes}",
                        quantity=1, unit_price=price, total_price=price
                    ))
                    
                elif i < len(hotel_data_list):
                    # Add new
                    h_data = hotel_data_list[i]
                    h_name = h_data.get('hotel_name', 'Unknown Hotel')
                    if not h_name.strip(): h_name = 'Unknown Hotel'
                    h_city = h_data.get('city', 'Unknown')
                    
                    cin = h_data.get('check_in_date', date.today())
                    cout = h_data.get('check_out_date', date.today())
                    if isinstance(cin, str):
                        try: cin = date.fromisoformat(cin)
                        except: cin = date.today()
                    if isinstance(cout, str):
                        try: cout = date.fromisoformat(cout)
                        except: cout = date.today()
                    nights = (cout - cin).days if cin and cout else 0
                    if nights > 0:
                        total_nights_calc += nights
                    
                    from models.hotel import Hotel
                    hotel_record = session.query(Hotel).filter(Hotel.hotel_name == h_name, Hotel.city == h_city).first()
                    if not hotel_record:
                        hotel_record = Hotel(
                            hotel_code=f"HT-{uuid.uuid4().hex[:6].upper()}",
                            hotel_name=h_name,
                            city=h_city,
                            country="Saudi Arabia" if h_city in ["Makkah", "Medinah", "Jeddah", "Taif"] else "Unknown"
                        )
                        session.add(hotel_record)
                        session.flush()
                        
                    hotel = HotelBooking(
                        booking_number=f"HTL-{uuid.uuid4().hex[:6].upper()}",
                        hotel_id=hotel_record.id,
                        customer_id=umrah.customer_id, umrah_booking_id=umrah.id,
                        city=h_city,
                        check_in_date=cin,
                        check_out_date=cout,
                        total_selling=float(h_data.get('sales_price', 0)), notes=h_name,
                        hn_number=h_data.get('hn_number', None),
                        reservation_name=h_data.get('reservation_name', None),
                        hotel_name_override=h_data.get('hotel_name', None),
                        room_type=h_data.get('room_type', 'DOUBLE'),
                        num_rooms=int(h_data.get('rooms_count', 1)),
                        purchase_price=float(h_data.get('purchase_price', 0)),
                        sales_price=float(h_data.get('sales_price', 0)),
                        profit=float(h_data.get('profit', 0))
                    )
                    session.add(hotel)
                    
                    price = float(hotel.total_selling)
                    total_amount += price
                    new_invoice_items.append(InvoiceItem(
                        description=f"Hotel [{hotel.city}] - {hotel.notes}",
                        quantity=1, unit_price=price, total_price=price
                    ))
                    
                else:
                    # Remove left over
                    session.delete(existing_hotels[i])
            
            if total_nights_calc > 0:
                umrah.total_nights = total_nights_calc
                
            # Transport
            transport_data_list = new_data_payload.get('transport', [])
            for transport_data in transport_data_list:
                if not transport_data.get('exclude_invoice'):
                    price = float(transport_data.get('sales_price', 0))
                    total_amount += price
                    new_invoice_items.append(InvoiceItem(
                        description=f"Transport - {transport_data.get('type', 'Standard')}",
                        quantity=1, unit_price=price, total_price=price
                    ))

            umrah.final_total_price = total_amount
            
            # Update Centralized Booking Record — categorical pricing (Phase 1/3)
            stmt_booking = select(Booking).where(Booking.package_id == umrah.id)
            booking = session.scalars(stmt_booking).first()
            if booking:
                booking.adult_count          = new_data_payload.get('adult_count', booking.adult_count)
                booking.adult_cost_price     = new_data_payload.get('adult_cost_price', booking.adult_cost_price)
                booking.adult_selling_price  = new_data_payload.get('adult_selling_price', booking.adult_selling_price)
                booking.child_count          = new_data_payload.get('child_count', booking.child_count)
                booking.child_cost_price     = new_data_payload.get('child_cost_price', booking.child_cost_price)
                booking.child_selling_price  = new_data_payload.get('child_selling_price', booking.child_selling_price)
                booking.infant_count         = new_data_payload.get('infant_count', booking.infant_count)
                booking.infant_cost_price    = new_data_payload.get('infant_cost_price', booking.infant_cost_price)
                booking.infant_selling_price = new_data_payload.get('infant_selling_price', booking.infant_selling_price)
                if 'payment_method' in new_data_payload:
                    booking.payment_method = new_data_payload['payment_method']

            
            # 4. Invoice Diff
            stmt = select(Invoice).where(Invoice.reference_id == umrah.id)
            invoice = session.scalars(stmt).first()
            
            if invoice:
                # Delete old items
                for item in invoice.items:
                    session.delete(item)
                
                # Add new items
                for item in new_invoice_items:
                    item.invoice_id = invoice.id
                    session.add(item)
                
                # Re-balance Invoice
                old_total = float(invoice.total_amount or 0)
                invoice.subtotal = float(total_amount)
                invoice.total_amount = float(total_amount)
                
                # If price changed, we adjust the balance_due (amount_remaining)
                diff = float(total_amount) - old_total
                new_balance = float(invoice.amount_remaining or 0) + diff
                
                invoice.amount_remaining = max(0.0, float(new_balance))
                
                # Adjust status based on new balance vs amount paid
                if invoice.amount_remaining <= 0 and invoice.amount_paid > 0:
                    invoice.status = "Paid"
                elif invoice.amount_paid > 0:
                    invoice.status = "Partial"
                else:
                    invoice.status = "Unpaid"
                    
            session.commit()
            return umrah
        except Exception as e:
            session.rollback()
            raise e
