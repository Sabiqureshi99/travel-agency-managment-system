import sys
import traceback
sys.path.append('.')
from config.database import get_session
from repositories.flight_repository import FlightBookingRepository

with get_session() as session:
    repo = FlightBookingRepository(session)
    res = repo.search_flights(limit=1)
    flight = res['items'][0] if res['items'] else None
    
    if flight:
        try:
            print(f'Flight ID: {flight.id}')
            print(f'Customer: {flight.customer}')
            print(f'Segments: {flight.segments}')
            print(f'Trip Type: {flight.trip_type}')
            print(f'Base Fare: {flight.base_fare}')
        except Exception as e:
            traceback.print_exc()
