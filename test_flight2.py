import sys
import traceback
sys.path.append('.')
from config.database import get_session
from repositories.flight_repository import FlightBookingRepository
from models.flight import FlightBooking

with get_session() as session:
    flights = session.query(FlightBooking).all()
    for flight in flights:
        print(f"Flight ID: {flight.id}, PNR: {flight.pnr}, Segments: {len(flight.segments)}, Passengers: {len(flight.passengers)}")
