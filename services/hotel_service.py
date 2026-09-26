import logging
from typing import List, Optional, Dict, Any
from core.base_service import BaseService
from models.hotel import Hotel, HotelBooking
from repositories.hotel_repository import HotelRepository, HotelBookingRepository
from core.base_model import generate_uuid

logger = logging.getLogger(__name__)


class HotelService(BaseService):
    """Service for managing hotels and hotel bookings."""

    def __init__(self):
        super().__init__()

    # ─── Hotel CRUD ──────────────────────────────────────────────────────────

    def search_hotels(self, query: str = "", skip: int = 0, limit: int = 50) -> dict:
        """Search hotels with pagination."""
        with self._get_session() as session:
            repo = HotelRepository(session)
            return repo.search_hotels(query=query, skip=skip, limit=limit)

    def create_hotel(self, hotel_data: Dict[str, Any], created_by: Optional[str] = None) -> Hotel:
        """Create a new hotel record."""
        self.validate_required(hotel_data, ['hotel_name', 'city', 'country'])
        with self._get_session() as session:
            repo = HotelRepository(session)
            count = repo.get_count()
            if 'hotel_code' not in hotel_data or not hotel_data['hotel_code']:
                hotel_data['hotel_code'] = f"HTL-{count + 1:04d}"
            self.validate_unique(session, Hotel, 'hotel_code', hotel_data['hotel_code'])
            hotel = Hotel(id=generate_uuid(), created_by=created_by)
            for k, v in hotel_data.items():
                if hasattr(hotel, k):
                    setattr(hotel, k, v)
            repo.add(hotel)
            session.commit()
            session.refresh(hotel)
            logger.info(f"Created hotel: {hotel.hotel_code}")
            return hotel

    def get_hotel_by_id(self, hotel_id: str) -> Optional[Hotel]:
        with self._get_session() as session:
            return HotelRepository(session).get_by_id(hotel_id)

    def update_hotel(self, hotel_id: str, hotel_data: Dict[str, Any], updated_by: Optional[str] = None) -> Hotel:
        with self._get_session() as session:
            repo = HotelRepository(session)
            hotel = repo.get_by_id(hotel_id)
            if not hotel:
                raise ValueError(f"Hotel {hotel_id} not found.")
            for k, v in hotel_data.items():
                if hasattr(hotel, k) and k not in ('id', 'created_at', 'created_by', 'hotel_code'):
                    setattr(hotel, k, v)
            hotel.updated_by = updated_by
            repo.update(hotel)
            session.commit()
            session.refresh(hotel)
            return hotel

    def delete_hotel(self, hotel_id: str, deleted_by: Optional[str] = None) -> bool:
        with self._get_session() as session:
            repo = HotelRepository(session)
            hotel = repo.get_by_id(hotel_id)
            if not hotel:
                raise ValueError(f"Hotel {hotel_id} not found.")
            repo.soft_delete(hotel, deleted_by=deleted_by)
            session.commit()
            return True

    # ─── Hotel Booking CRUD ──────────────────────────────────────────────────

    def search_hotel_bookings(self, query: str = "", skip: int = 0, limit: int = 50) -> dict:
        """Search hotel bookings with pagination."""
        with self._get_session() as session:
            repo = HotelBookingRepository(session)
            return repo.search_hotel_bookings(query=query, skip=skip, limit=limit)

    def create_hotel_booking(self, booking_data: Dict[str, Any], created_by: Optional[str] = None) -> HotelBooking:
        """Create a new hotel booking."""
        self.validate_required(booking_data, ['hotel_id', 'customer_id', 'check_in_date', 'check_out_date'])
        with self._get_session() as session:
            repo = HotelBookingRepository(session)
            count = repo.get_count()
            if 'booking_number' not in booking_data or not booking_data['booking_number']:
                booking_data['booking_number'] = f"HBK-{count + 1:05d}"
            self.validate_unique(session, HotelBooking, 'booking_number', booking_data['booking_number'])
            booking = HotelBooking(id=generate_uuid(), created_by=created_by)
            for k, v in booking_data.items():
                if hasattr(booking, k):
                    setattr(booking, k, v)
            repo.add(booking)
            session.commit()
            session.refresh(booking)
            logger.info(f"Created hotel booking: {booking.booking_number}")
            return booking

    def update_hotel_booking(self, booking_id: str, booking_data: Dict[str, Any], updated_by: Optional[str] = None) -> HotelBooking:
        with self._get_session() as session:
            repo = HotelBookingRepository(session)
            booking = repo.get_by_id(booking_id)
            if not booking:
                raise ValueError(f"Hotel Booking {booking_id} not found.")
            for k, v in booking_data.items():
                if hasattr(booking, k) and k not in ('id', 'created_at', 'created_by', 'booking_number'):
                    setattr(booking, k, v)
            booking.updated_by = updated_by
            repo.update(booking)
            session.commit()
            session.refresh(booking)
            return booking

    def cancel_hotel_booking(self, booking_id: str, deleted_by: Optional[str] = None) -> bool:
        with self._get_session() as session:
            repo = HotelBookingRepository(session)
            booking = repo.get_by_id(booking_id)
            if not booking:
                raise ValueError(f"Hotel Booking {booking_id} not found.")
            repo.soft_delete(booking, deleted_by=deleted_by)
            session.commit()
            return True
