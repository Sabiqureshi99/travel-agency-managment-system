import logging
from typing import List, Optional, Dict, Any
from core.base_service import BaseService
from models.flight import FlightBooking, FlightPassenger, FlightSegment
from repositories.flight_repository import FlightBookingRepository, FlightPassengerRepository
from core.base_model import generate_uuid

logger = logging.getLogger(__name__)

class FlightService(BaseService):
    """Service for managing flight bookings and schedules in the travel agency."""

    def __init__(self):
        super().__init__()

    def search_flights(self, query: str = "", fields: list[str] | None = None, skip: int = 0, limit: int = 50) -> dict:
        """Search flights with pagination, sorting, and field filtering."""
        with self._get_session() as session:
            repo = FlightBookingRepository(session)
            return repo.search_flights(query=query, fields=fields, skip=skip, limit=limit)

    def book_flight(self, booking_data: Dict[str, Any], passengers_data: List[Dict[str, Any]], created_by: Optional[str] = None) -> FlightBooking:
        """
        Books a new flight.
        """
        self.validate_required(booking_data, ['customer_id', 'flight_type', 'trip_type'])
        
        with self._get_session() as session:
            repo = FlightBookingRepository(session)
            passenger_repo = FlightPassengerRepository(session)
            
            # Auto-generate booking number if not provided
            if 'booking_number' not in booking_data or not booking_data['booking_number']:
                count = repo.get_count()
                booking_data['booking_number'] = f"FLT-{count + 1:05d}"
                
            self.validate_unique(session, FlightBooking, 'booking_number', booking_data['booking_number'])
            
            from datetime import date as _date
            # Ensure non-nullable fields always have a value
            booking_data.setdefault('origin', '')
            booking_data.setdefault('destination', '')
            booking_data.setdefault('airline', 'Unknown')
            booking_data.setdefault('departure_date', _date.today())
                
            # Create Flight Booking
            booking = FlightBooking(id=generate_uuid(), created_by=created_by)
            for key, value in booking_data.items():
                if hasattr(booking, key):
                    setattr(booking, key, value)
                    
            repo.add(booking)
            
            # Add passengers
            if passengers_data:
                for pax in passengers_data:
                    passenger = FlightPassenger(
                        id=generate_uuid(),
                        booking_id=booking.id,
                        created_by=created_by
                    )
                    for k, v in pax.items():
                        if hasattr(passenger, k):
                            setattr(passenger, k, v)
                    session.add(passenger)
                    
            session.commit()
            session.refresh(booking)
            logger.info(f"Booked flight: {booking.booking_number}")
            return booking

    def get_flight_by_id(self, flight_id: str):
        """Retrieves a flight booking by ID."""
        with self._get_session() as session:
            repo = FlightBookingRepository(session)
            return repo.get_by_id(flight_id)

    def update_flight(self, flight_id: str, booking_data: Dict[str, Any], passengers_data: List[Dict[str, Any]] | None = None, updated_by: Optional[str] = None):
        """Updates an existing flight booking."""
        with self._get_session() as session:
            repo = FlightBookingRepository(session)
            booking = repo.get_by_id(flight_id)
            if not booking:
                raise ValueError(f"Flight Booking with ID {flight_id} not found.")
                
            if 'booking_number' in booking_data and booking_data['booking_number']:
                self.validate_unique(session, FlightBooking, 'booking_number', booking_data['booking_number'], exclude_id=flight_id)
                
            for key, value in booking_data.items():
                if hasattr(booking, key) and key not in ('id', 'created_at', 'created_by', 'booking_number'):
                    setattr(booking, key, value)
                    
            if passengers_data is not None:
                for p in list(booking.passengers):
                    session.delete(p)
                booking.passengers.clear()
                
                for pax in passengers_data:
                    passenger = FlightPassenger(
                        id=generate_uuid(),
                        booking_id=booking.id,
                        created_by=updated_by
                    )
                    for k, v in pax.items():
                        if hasattr(passenger, k):
                            setattr(passenger, k, v)
                    session.add(passenger)
                    
            booking.updated_by = updated_by
            repo.update(booking)
            session.commit()
            session.refresh(booking)
            logger.info(f"Updated flight booking ID {flight_id}")
            return booking

    def cancel_flight(self, flight_id: str, deleted_by: Optional[str] = None) -> bool:
        """Soft deletes (cancels) a flight booking."""
        with self._get_session() as session:
            repo = FlightBookingRepository(session)
            booking = repo.get_by_id(flight_id)
            if not booking:
                raise ValueError(f"Flight Booking with ID {flight_id} not found.")
            
            repo.soft_delete(booking, deleted_by=deleted_by or 'system')
            session.commit()
            logger.info(f"Canceled flight booking ID {flight_id}")
            return True
