from typing import List, Optional
from models.vendor import Vendor
from repositories.vendor_repository import VendorRepository
from core.enums import VendorType

class VendorService:
    def __init__(self, repository: VendorRepository):
        self.repo = repository

    def add_vendor(self, name: str, vendor_type: VendorType, 
                   contact_person: Optional[str] = None, 
                   phone: Optional[str] = None, 
                   email: Optional[str] = None,
                   makkah_helpline_phone: Optional[str] = None,
                   makkah_helpline_whatsapp: Optional[str] = None,
                   madinah_helpline_phone: Optional[str] = None,
                   madinah_helpline_whatsapp: Optional[str] = None) -> Vendor:
        # Simple auto-generate code logic (e.g. V-001)
        count = len(self.repo.get_all()) + 1
        code = f"V-{count:03d}"
        
        vendor = Vendor(
            vendor_code=code,
            company_name=name,
            vendor_type=vendor_type,
            contact_person=contact_person,
            phone=phone,
            email=email,
            makkah_helpline_phone=makkah_helpline_phone,
            makkah_helpline_whatsapp=makkah_helpline_whatsapp,
            madinah_helpline_phone=madinah_helpline_phone,
            madinah_helpline_whatsapp=madinah_helpline_whatsapp
        )
        return self.repo.add(vendor)

    def get_all_vendors(self) -> List[Vendor]:
        return self.repo.get_all()

    def search_vendors_paginated(self, query: str = "", skip: int = 0, limit: int = 100, vendor_type: Optional[str] = None) -> tuple[List[Vendor], int]:
        return self.repo.search_paginated(query, skip, limit, vendor_type)

    def update_vendor(self, vendor: Vendor, name: str, vendor_type: VendorType,
                      contact_person: Optional[str] = None, phone: Optional[str] = None,
                      email: Optional[str] = None,
                      makkah_helpline_phone: Optional[str] = None,
                      makkah_helpline_whatsapp: Optional[str] = None,
                      madinah_helpline_phone: Optional[str] = None,
                      madinah_helpline_whatsapp: Optional[str] = None) -> Vendor:
        vendor.company_name = name
        vendor.vendor_type = vendor_type
        vendor.contact_person = contact_person
        vendor.phone = phone
        vendor.email = email
        vendor.makkah_helpline_phone = makkah_helpline_phone
        vendor.makkah_helpline_whatsapp = makkah_helpline_whatsapp
        vendor.madinah_helpline_phone = madinah_helpline_phone
        vendor.madinah_helpline_whatsapp = madinah_helpline_whatsapp
        return self.repo.update(vendor)

    def delete_vendor(self, vendor: Vendor) -> None:
        self.repo.delete(vendor)
