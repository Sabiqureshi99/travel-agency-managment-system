import logging
from typing import List, Optional, Dict, Any
from core.base_service import BaseService
from models.customer import Customer, CustomerFamilyMember, CustomerEmergencyContact
from repositories.customer_repository import CustomerRepository
from core.base_model import generate_uuid
import uuid

logger = logging.getLogger(__name__)

class CustomerService(BaseService):
    """Service for managing customers in the travel agency."""

    def __init__(self):
        super().__init__()

    def create_customer(self, customer_data: Dict[str, Any], created_by: Optional[str] = None) -> Customer:
        """
        Creates a new customer.
        
        Args:
            customer_data (Dict[str, Any]): Dictionary containing customer details.
            created_by (str, optional): User ID of the creator.
            
        Returns:
            Customer: Created customer object.
        """
        self.validate_required(customer_data, ['first_name', 'phone_primary'])
        
        with self._get_session() as session:
            repo = CustomerRepository(session)
            
            # Auto-generate customer code if not provided
            if 'customer_code' not in customer_data or not customer_data['customer_code']:
                count = repo.get_count()
                customer_data['customer_code'] = f"CUST-{count + 1:04d}"
                
            # Check unique fields
            if 'cnic' in customer_data and customer_data['cnic']:
                self.validate_unique(session, Customer, 'cnic', customer_data['cnic'])
            if 'passport_number' in customer_data and customer_data['passport_number']:
                self.validate_unique(session, Customer, 'passport_number', customer_data['passport_number'])
                
            # Create instance
            customer = Customer(id=generate_uuid(), created_by=created_by)
            # Extract child lists
            family_data = customer_data.pop('family_members', [])
            emergency_data = customer_data.pop('emergency_contacts', [])

            for key, value in customer_data.items():
                if hasattr(customer, key):
                    setattr(customer, key, value)
                    
            repo.add(customer)
            
            # Save children
            for fam in family_data:
                fm = CustomerFamilyMember(id=generate_uuid(), customer_id=customer.id, created_by=created_by)
                for k, v in fam.items():
                    if hasattr(fm, k):
                        setattr(fm, k, v)
                session.add(fm)
                
            for em in emergency_data:
                ec = CustomerEmergencyContact(id=generate_uuid(), customer_id=customer.id, created_by=created_by)
                for k, v in em.items():
                    if hasattr(ec, k):
                        setattr(ec, k, v)
                session.add(ec)
                
            session.commit()
            session.refresh(customer)
            logger.info(f"Created customer: {customer.full_name} ({customer.customer_code})")
            return customer

    def get_customer_by_id(self, customer_id: str) -> Optional[Customer]:
        """
        Retrieves a customer by ID.
        """
        with self._get_session() as session:
            repo = CustomerRepository(session)
            return repo.get_by_id(customer_id)

    def update_customer(self, customer_id: str, customer_data: Dict[str, Any], updated_by: Optional[str] = None) -> Customer:
        """
        Updates an existing customer.
        """
        with self._get_session() as session:
            repo = CustomerRepository(session)
            customer = repo.get_by_id(customer_id)
            if not customer:
                raise ValueError(f"Customer with ID {customer_id} not found.")
                
            # Check unique fields
            if 'cnic' in customer_data and customer_data['cnic']:
                self.validate_unique(session, Customer, 'cnic', customer_data['cnic'], exclude_id=customer_id)
            if 'passport_number' in customer_data and customer_data['passport_number']:
                self.validate_unique(session, Customer, 'passport_number', customer_data['passport_number'], exclude_id=customer_id)
                
            # Work on a copy so we don't mutate the caller's dict
            customer_data = dict(customer_data)
            
            # Extract child lists
            family_data = customer_data.pop('family_members', None)
            emergency_data = customer_data.pop('emergency_contacts', None)

            for key, value in customer_data.items():
                if hasattr(customer, key) and key not in ('id', 'created_at', 'created_by', 'customer_code'):
                    setattr(customer, key, value)
                    
            if family_data is not None:
                # Clear existing and re-add (for simplicity in editing)
                for old_fam in customer.family_members:
                    session.delete(old_fam)
                for fam in family_data:
                    fm = CustomerFamilyMember(id=generate_uuid(), customer_id=customer.id, created_by=updated_by)
                    for k, v in fam.items():
                        if hasattr(fm, k):
                            setattr(fm, k, v)
                    session.add(fm)
                    
            if emergency_data is not None:
                for old_em in customer.emergency_contacts:
                    session.delete(old_em)
                for em in emergency_data:
                    ec = CustomerEmergencyContact(id=generate_uuid(), customer_id=customer.id, created_by=updated_by)
                    for k, v in em.items():
                        if hasattr(ec, k):
                            setattr(ec, k, v)
                    session.add(ec)

            customer.updated_by = updated_by
            repo.update(customer)
            session.commit()
            session.refresh(customer)
            logger.info(f"Updated customer ID {customer_id}")
            return customer

    def delete_customer(self, customer_id: str, deleted_by: Optional[str] = None) -> bool:
        """
        Soft deletes a customer.
        """
        with self._get_session() as session:
            repo = CustomerRepository(session)
            customer = repo.get_by_id(customer_id)
            if not customer:
                raise ValueError(f"Customer with ID {customer_id} not found.")
            
            repo.soft_delete(customer, deleted_by=deleted_by)
            session.commit()
            logger.info(f"Deleted customer ID {customer_id}")
            return True

    def search_customers(self, query: str = "", fields: Optional[List[str]] = None, skip: int = 0, limit: int = 100) -> List[Customer]:
        """
        Searches customers.
        """
        with self._get_session() as session:
            repo = CustomerRepository(session)
            if query and fields:
                return repo.search(query, fields, skip, limit)
            else:
                return repo.get_all(skip, limit)

    def search_customers_paginated(self, query: str = "", fields: Optional[List[str]] = None, skip: int = 0, limit: int = 100) -> tuple[List[Customer], int]:
        """
        Searches customers and returns total count.
        """
        with self._get_session() as session:
            repo = CustomerRepository(session)
            if query and fields:
                return repo.search_paginated(query, fields, skip, limit)
            else:
                return repo.get_all_paginated(skip, limit)
