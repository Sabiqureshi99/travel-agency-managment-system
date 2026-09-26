import logging
from typing import List, Optional, Dict, Any
from core.base_service import BaseService
from models.visa import VisaApplication, VisaApplicant
from repositories.visa_repository import VisaApplicationRepository, VisaApplicantRepository
from core.base_model import generate_uuid

logger = logging.getLogger(__name__)

class VisaService(BaseService):
    """Service for managing visa applications in the travel agency."""

    def __init__(self):
        super().__init__()

    def search_visas(self, query: str = "", fields: list[str] | None = None, skip: int = 0, limit: int = 50) -> dict:
        """Search visas with pagination, sorting, and field filtering."""
        with self._get_session() as session:
            repo = VisaApplicationRepository(session)
            return repo.search_visas(query=query, fields=fields, skip=skip, limit=limit)

    def submit_application(self, application_data: Dict[str, Any], applicants_data: List[Dict[str, Any]], created_by: Optional[str] = None) -> VisaApplication:
        """
        Submits a new visa application.
        """
        self.validate_required(application_data, ['customer_id', 'country', 'visa_type', 'application_date'])
        
        with self._get_session() as session:
            repo = VisaApplicationRepository(session)
            applicant_repo = VisaApplicantRepository(session)
            
            # Auto-generate application number if not provided
            if 'application_number' not in application_data or not application_data['application_number']:
                count = repo.get_count()
                application_data['application_number'] = f"VSA-{count + 1:05d}"
                
            self.validate_unique(session, VisaApplication, 'application_number', application_data['application_number'])
            
            # Create Visa Application
            application = VisaApplication(id=generate_uuid(), created_by=created_by)
            for key, value in application_data.items():
                if hasattr(application, key):
                    setattr(application, key, value)
                    
            repo.add(application)
            
            # Add applicants
            if applicants_data:
                for app in applicants_data:
                    applicant = VisaApplicant(
                        id=generate_uuid(),
                        visa_application_id=application.id,
                        created_by=created_by
                    )
                    for k, v in app.items():
                        if hasattr(applicant, k):
                            setattr(applicant, k, v)
                    applicant_repo.add(applicant)
                    
            session.commit()
            session.refresh(application)
            logger.info(f"Submitted visa application: {application.application_number}")
            return application

    def get_application_by_id(self, application_id: str) -> Optional[VisaApplication]:
        """Retrieves a visa application by ID."""
        with self._get_session() as session:
            repo = VisaApplicationRepository(session)
            return repo.get_by_id(application_id)

    def update_application_status(self, application_id: str, application_data: Dict[str, Any], updated_by: Optional[str] = None) -> VisaApplication:
        """Updates an existing visa application."""
        with self._get_session() as session:
            repo = VisaApplicationRepository(session)
            application = repo.get_by_id(application_id)
            if not application:
                raise ValueError(f"Visa Application with ID {application_id} not found.")
                
            if 'application_number' in application_data and application_data['application_number']:
                self.validate_unique(session, VisaApplication, 'application_number', application_data['application_number'], exclude_id=application_id)
                
            # Work on a copy so we don't mutate the caller's dict
            application_data = dict(application_data)
            
            # Extract child lists
            applicants_data = application_data.pop('applicants', None)

            for key, value in application_data.items():
                if hasattr(application, key) and key not in ('id', 'created_at', 'created_by', 'application_number'):
                    setattr(application, key, value)
                    
            if applicants_data is not None:
                for old_app in application.applicants:
                    session.delete(old_app)
                for app in applicants_data:
                    new_app = VisaApplicant(id=generate_uuid(), visa_application_id=application.id, created_by=updated_by)
                    for k, v in app.items():
                        if hasattr(new_app, k):
                            setattr(new_app, k, v)
                    session.add(new_app)
                    
            application.updated_by = updated_by
            repo.update(application)
            session.commit()
            session.refresh(application)
            logger.info(f"Updated visa application ID {application_id}")
            return application

    def delete_application(self, application_id: str, deleted_by: Optional[str] = None) -> bool:
        """Soft deletes a visa application."""
        with self._get_session() as session:
            repo = VisaApplicationRepository(session)
            application = repo.get_by_id(application_id)
            if not application:
                raise ValueError(f"Visa Application with ID {application_id} not found.")
            
            repo.soft_delete(application, deleted_by=deleted_by)
            session.commit()
            logger.info(f"Deleted visa application ID {application_id}")
            return True
