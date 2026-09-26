from types import SimpleNamespace
from core.base_service import BaseService
from models.company_profile import CompanyProfile
from core.signals import app_signals

class CompanyProfileService(BaseService):
    def get_profile(self):
        with self._get_session() as session:
            profile = session.query(CompanyProfile).first()
            if not profile:
                profile = CompanyProfile()
                session.add(profile)
                session.commit()
                session.refresh(profile)
            # Return a plain object so all fields are safe outside the session
            return SimpleNamespace(
                company_name=profile.company_name,
                address=profile.address,
                phone=profile.phone,
                email=profile.email,
                website=profile.website,
                ntn=profile.ntn,
                strn=profile.strn,
                logo_data=bytes(profile.logo_data) if profile.logo_data else None,
            )

    def save_profile(self, data: dict):
        with self._get_session() as session:
            profile = session.query(CompanyProfile).first()
            if not profile:
                profile = CompanyProfile()
                session.add(profile)
                
            if 'company_name' in data: profile.company_name = data['company_name']
            if 'phone' in data: profile.phone = data['phone']
            if 'email' in data: profile.email = data['email']
            if 'address' in data: profile.address = data['address']
            if 'ntn' in data: profile.ntn = data['ntn']
            if 'strn' in data: profile.strn = data['strn']
            if 'website' in data: profile.website = data['website']
            if 'logo_data' in data: profile.logo_data = data['logo_data']
            
            session.commit()
            session.refresh(profile)
            
            # Emit the global signal so Sidebar can update instantly
            app_signals.company_profile_updated.emit()
            return profile
