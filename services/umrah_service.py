import logging
from typing import List, Optional, Dict, Any
from core.base_service import BaseService
from models.umrah import UmrahPackageTemplate, UmrahPackagePricing, CustomUmrahBooking, UmrahPilgrim
from repositories.umrah_repository import (
    UmrahPackageTemplateRepository, 
    UmrahPackagePricingRepository,
    CustomUmrahBookingRepository,
    UmrahPilgrimRepository
)
from core.base_model import generate_uuid

logger = logging.getLogger(__name__)


class UmrahService(BaseService):
    """Service for managing Umrah package templates and custom bookings."""

    def __init__(self):
        super().__init__()

    # ─── Template CRUD ────────────────────────────────────────────────────────
    
    def search_templates(self, query: str = "", skip: int = 0, limit: int = 50) -> dict:
        with self._get_session() as session:
            repo = UmrahPackageTemplateRepository(session)
            return repo.search_templates(query=query, skip=skip, limit=limit)

    def create_master_template(self, template_data: Dict[str, Any], pricing_matrix: List[Dict[str, Any]], created_by: Optional[str] = None) -> UmrahPackageTemplate:
        """Create a master template with its pricing matrix in one transaction."""
        self.validate_required(template_data, ['name', 'total_nights'])
        
        with self._get_session() as session:
            template_repo = UmrahPackageTemplateRepository(session)
            pricing_repo = UmrahPackagePricingRepository(session)
            
            template = UmrahPackageTemplate(id=generate_uuid(), created_by=created_by)
            for k, v in template_data.items():
                if hasattr(template, k):
                    setattr(template, k, v)
            
            template_repo.add(template)
            
            for row in pricing_matrix:
                self.validate_required(row, ['room_type', 'price_per_person'])
                pricing = UmrahPackagePricing(
                    id=generate_uuid(),
                    template_id=template.id,
                    created_by=created_by,
                    room_type=row['room_type'],
                    price_per_person=row['price_per_person']
                )
                pricing_repo.add(pricing)
                
            session.commit()
            session.refresh(template)
            logger.info(f"Created master template: {template.name}")
            return template

    def get_template_by_id(self, template_id: str) -> Optional[UmrahPackageTemplate]:
        with self._get_session() as session:
            return UmrahPackageTemplateRepository(session).get_by_id(template_id)
            
    def get_pricing_for_template(self, template_id: str) -> List[UmrahPackagePricing]:
        """Fetch all pricing matrix rows for a template."""
        with self._get_session() as session:
            return UmrahPackagePricingRepository(session).get_all_by_field('template_id', template_id)

    def update_master_template(self, template_id: str, template_data: Dict[str, Any], pricing_matrix: List[Dict[str, Any]], updated_by: Optional[str] = None) -> UmrahPackageTemplate:
        self.validate_required(template_data, ['name', 'total_nights'])
        
        with self._get_session() as session:
            template_repo = UmrahPackageTemplateRepository(session)
            pricing_repo = UmrahPackagePricingRepository(session)
            
            template = template_repo.get_by_id(template_id)
            if not template:
                raise ValueError(f"Template {template_id} not found.")
                
            for k, v in template_data.items():
                if hasattr(template, k) and k not in ('id', 'created_at', 'created_by'):
                    setattr(template, k, v)
            template.updated_by = updated_by
            template_repo.update(template)
            
            # Recreate pricing
            old_pricing = pricing_repo.get_all_by_field('template_id', template_id)
            for op in old_pricing:
                session.delete(op)
                
            for row in pricing_matrix:
                self.validate_required(row, ['room_type', 'price_per_person'])
                pricing = UmrahPackagePricing(
                    id=generate_uuid(),
                    template_id=template.id,
                    created_by=updated_by,
                    room_type=row['room_type'],
                    price_per_person=row['price_per_person']
                )
                pricing_repo.add(pricing)
                
            session.commit()
            session.refresh(template)
            logger.info(f"Updated master template: {template.name}")
            return template

    def delete_master_template(self, template_id: str, deleted_by: Optional[str] = None) -> bool:
        with self._get_session() as session:
            repo = UmrahPackageTemplateRepository(session)
            template = repo.get_by_id(template_id)
            if not template:
                raise ValueError(f"Template {template_id} not found.")
            repo.soft_delete(template, deleted_by=deleted_by)
            session.commit()
            return True

    # ─── Custom Booking CRUD ──────────────────────────────────────────────────

    def search_bookings(self, query: str = "", skip: int = 0, limit: int = 50) -> dict:
        with self._get_session() as session:
            repo = CustomUmrahBookingRepository(session)
            return repo.search_bookings(query=query, skip=skip, limit=limit)

    def calculate_booking_total(self, base_package_price: float, airfare_price: float, total_pilgrims: int, supplements: dict) -> float:
        """Calculates final total: ((Base Price + Airfare) * Pilgrims) + Sum(Supplements)"""
        supp_total = sum([float(v) for v in supplements.values()]) if supplements else 0
        return ((base_package_price + airfare_price) * total_pilgrims) + supp_total

    def create_custom_booking(self, booking_data: Dict[str, Any], pilgrims_data: List[Dict[str, Any]], created_by: Optional[str] = None) -> CustomUmrahBooking:
        self.validate_required(booking_data, ['customer_id', 'booking_date', 'base_package_price', 'total_pilgrims'])
        
        with self._get_session() as session:
            booking_repo = CustomUmrahBookingRepository(session)
            pilgrim_repo = UmrahPilgrimRepository(session)
            
            count = booking_repo.get_count()
            if 'booking_number' not in booking_data or not booking_data['booking_number']:
                booking_data['booking_number'] = f"UMR-{count + 1:04d}"
                
            self.validate_unique(session, CustomUmrahBooking, 'booking_number', booking_data['booking_number'])
            
            booking = CustomUmrahBooking(id=generate_uuid(), created_by=created_by)
            for k, v in booking_data.items():
                if hasattr(booking, k):
                    setattr(booking, k, v)
                    
            # Safe calculation on backend side
            supplements = booking_data.get('supplements', {})
            booking.final_total_price = self.calculate_booking_total(
                booking.base_package_price, 
                booking.airfare_price, 
                booking.total_pilgrims, 
                supplements
            )
            
            booking_repo.add(booking)
            
            for p_data in pilgrims_data:
                self.validate_required(p_data, ['full_name', 'passport_number', 'gender'])
                pilgrim = UmrahPilgrim(
                    id=generate_uuid(),
                    booking_id=booking.id,
                    created_by=created_by
                )
                for pk, pv in p_data.items():
                    if hasattr(pilgrim, pk):
                        setattr(pilgrim, pk, pv)
                pilgrim_repo.add(pilgrim)
                
            session.commit()
            session.refresh(booking)
            logger.info(f"Created Custom Umrah booking: {booking.booking_number}")
            return booking

    def update_custom_booking(self, booking_id: str, booking_data: Dict[str, Any], updated_by: Optional[str] = None) -> CustomUmrahBooking:
        with self._get_session() as session:
            repo = CustomUmrahBookingRepository(session)
            booking = repo.get_by_id(booking_id)
            if not booking:
                raise ValueError(f"Booking {booking_id} not found.")
                
            for k, v in booking_data.items():
                if hasattr(booking, k) and k not in ('id', 'created_at', 'created_by', 'booking_number'):
                    setattr(booking, k, v)
                    
            # Safe calculation
            supplements = booking_data.get('supplements', booking.supplements or {})
            booking.final_total_price = self.calculate_booking_total(
                booking.base_package_price, 
                booking.airfare_price, 
                booking.total_pilgrims, 
                supplements
            )
                    
            booking.updated_by = updated_by
            repo.update(booking)
            session.commit()
            session.refresh(booking)
            return booking

    def delete_custom_booking(self, booking_id: str, deleted_by: Optional[str] = None) -> bool:
        with self._get_session() as session:
            repo = CustomUmrahBookingRepository(session)
            booking = repo.get_by_id(booking_id)
            if not booking:
                raise ValueError(f"Booking {booking_id} not found.")
            repo.soft_delete(booking, deleted_by=deleted_by)
            session.commit()
            return True
