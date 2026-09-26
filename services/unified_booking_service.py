from sqlalchemy.orm import Session
from models.booking import Booking
from models.pax import Pax
from models.hotel import HotelBooking
from models.transport import TransportBooking
from models.vendor import Vendor, VendorLedger
from models.accounting import Invoice, InvoiceItem
from datetime import date
import json

class UnifiedBookingService:
    def __init__(self, session: Session):
        self.session = session

    def save_unified_booking(self, customer_id: str, booking_data: dict, pax_list: list[dict], services: dict) -> Booking:
        # 1. Create Master Booking
        master_booking = Booking(
            customer_id=customer_id,
            booking_type="Unified",
            cost_price=booking_data.get('cost_price', 0),
            selling_price=booking_data.get('selling_price', 0)
        )
        self.session.add(master_booking)
        self.session.flush() # Get booking ID

        # 2. Process PAX and Identify Group Leader
        group_leader = None
        for pax_data in pax_list:
            pax = Pax(
                booking_id=master_booking.id,
                first_name=pax_data['first_name'],
                last_name=pax_data['last_name'],
                passport_number=pax_data.get('passport'),
                cnic=pax_data.get('cnic'),
                is_group_leader=pax_data.get('is_group_leader', False),
                linked_customer_id=pax_data.get('linked_customer_id')
            )
            if pax_data.get('dob'):
                pax.date_of_birth = pax_data['dob']
                
            self.session.add(pax)
            if pax.is_group_leader:
                group_leader = pax
                
        # Fallback to the main customer if no group leader is explicitly toggled
        billing_entity_id = group_leader.linked_customer_id if (group_leader and group_leader.linked_customer_id) else customer_id

        # 3. Generate Invoice Grouped to the Leader
        self._generate_group_invoice(master_booking, billing_entity_id, services, pax_list)

        # 4. Process Services & Vendor Ledgers
        if 'hotel' in services:
            self._process_hotel_service(master_booking, services['hotel'])
            
        if 'transport' in services:
            self._process_transport_service(master_booking, services['transport'])

        self.session.commit()
        return master_booking

    def _generate_group_invoice(self, booking: Booking, billing_customer_id: str, services: dict, pax_list: list[dict]):
        invoice = Invoice(
            invoice_number=f"INV-{booking.id[:6].upper()}",
            customer_id=billing_customer_id,
            issue_date=date.today(),
            total_amount=booking.selling_price,
            amount_remaining=booking.selling_price
        )
        self.session.add(invoice)
        self.session.flush()

        # Generate item-wise breakdown for the invoice
        if 'hotel' in services:
            hotel_data = services['hotel']
            item = InvoiceItem(
                invoice_id=invoice.id,
                description=f"Hotel Booking - {hotel_data['check_in_date']} to {hotel_data['check_out_date']}",
                quantity=1,
                unit_price=hotel_data.get('selling_price', 0),
                total_price=hotel_data.get('selling_price', 0)
            )
            self.session.add(item)
            
        if 'transport' in services:
            trans_data = services['transport']
            item = InvoiceItem(
                invoice_id=invoice.id,
                description=f"Transport Service - {trans_data.get('pickup_location')} to {trans_data.get('dropoff_location')}",
                quantity=1,
                unit_price=trans_data.get('selling_price', 0),
                total_price=trans_data.get('selling_price', 0)
            )
            self.session.add(item)
            
        # Add a base package fee if the sum of items doesn't match total selling price
        # Or you can add individual PAX processing fees here.

    def _process_hotel_service(self, booking: Booking, hotel_data: dict):
        hotel_booking = HotelBooking(
            booking_number=f"HB-{booking.id[:6].upper()}",
            customer_id=booking.customer_id,
            hotel_id=hotel_data['hotel_id'],
            vendor_id=hotel_data['vendor_id'],
            check_in_date=hotel_data['check_in_date'],
            check_out_date=hotel_data['check_out_date'],
            purchase_price=hotel_data['cost_price']
        )
        self.session.add(hotel_booking)
        self.session.flush()
        
        # Automatic Vendor Ledger Posting
        ledger_entry = VendorLedger(
            vendor_id=hotel_data['vendor_id'],
            credit=hotel_data['cost_price'],  # Credit the vendor for Cost of Goods Sold
            reference_booking_id=booking.id,
            description=f"Hotel Service COGS for Booking {booking.id[:6].upper()}"
        )
        self.session.add(ledger_entry)

        # 3. Voucher Generation Prep (Inject Vendor Contacts)
        self._inject_voucher_contacts(hotel_data['vendor_id'], booking)

    def _process_transport_service(self, booking: Booking, transport_data: dict):
        transport_booking = TransportBooking(
            booking_number=f"TB-{booking.id[:6].upper()}",
            customer_id=booking.customer_id,
            vehicle_id=transport_data.get('vehicle_id'),
            vendor_id=transport_data['vendor_id'],
            booking_date=date.today(),
            pickup_location=transport_data.get('pickup_location', 'N/A'),
            dropoff_location=transport_data.get('dropoff_location', 'N/A'),
            pickup_date=transport_data['pickup_date'],
            pickup_time=transport_data.get('pickup_time', '00:00'),
            purchase_price=transport_data['cost_price']
        )
        self.session.add(transport_booking)
        self.session.flush()

        # Automatic Vendor Ledger Posting
        ledger_entry = VendorLedger(
            vendor_id=transport_data['vendor_id'],
            credit=transport_data['cost_price'],  # Credit the vendor for Cost of Goods Sold
            reference_booking_id=booking.id,
            description=f"Transport Service COGS for Booking {booking.id[:6].upper()}"
        )
        self.session.add(ledger_entry)
        
        self._inject_voucher_contacts(transport_data['vendor_id'], booking)

    def _inject_voucher_contacts(self, vendor_id: str, booking: Booking):
        vendor = self.session.query(Vendor).get(vendor_id)
        if vendor:
            # We store this dynamically in the booking details JSON for the UI to use when printing
            details = booking.details or "{}"
            if isinstance(details, str):
                try:
                    details_dict = json.loads(details)
                except Exception:
                    details_dict = {}
            else:
                details_dict = details
                
            details_dict['makkah_contact'] = vendor.makkah_contact
            details_dict['madinah_contact'] = vendor.madinah_contact
            booking.details = json.dumps(details_dict)
