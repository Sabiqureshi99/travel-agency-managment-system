from typing import List, Optional
from sqlalchemy.orm import Session
from models.vendor import Vendor

class VendorRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(self, vendor: Vendor) -> Vendor:
        self.session.add(vendor)
        self.session.commit()
        self.session.refresh(vendor)
        return vendor

    def get_by_id(self, vendor_id: str) -> Optional[Vendor]:
        return self.session.query(Vendor).filter(Vendor.id == vendor_id).first()

    def get_all(self) -> List[Vendor]:
        return self.session.query(Vendor).all()

    def get_all_paginated(self, skip: int = 0, limit: int = 100, vendor_type: Optional[str] = None) -> tuple[List[Vendor], int]:
        query = self.session.query(Vendor)
        if vendor_type and vendor_type != "All":
            query = query.filter(Vendor.vendor_type == vendor_type)
        total = query.count()
        data = query.offset(skip).limit(limit).all()
        return data, total

    def search_paginated(self, query_str: str, skip: int = 0, limit: int = 100, vendor_type: Optional[str] = None) -> tuple[List[Vendor], int]:
        if not query_str:
            return self.get_all_paginated(skip, limit, vendor_type)
        from sqlalchemy import or_
        query = self.session.query(Vendor).filter(
            or_(
                Vendor.company_name.ilike(f"%{query_str}%"),
                Vendor.contact_person.ilike(f"%{query_str}%")
            )
        )
        if vendor_type and vendor_type != "All":
            query = query.filter(Vendor.vendor_type == vendor_type)
        total = query.count()
        data = query.offset(skip).limit(limit).all()
        return data, total

    def update(self, vendor: Vendor) -> Vendor:
        self.session.commit()
        self.session.refresh(vendor)
        return vendor

    def delete(self, vendor: Vendor) -> None:
        self.session.delete(vendor)
        self.session.commit()
