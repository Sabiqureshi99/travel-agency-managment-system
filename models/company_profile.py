from sqlalchemy import Column, String, LargeBinary
from core.base_model import BaseModel

class CompanyProfile(BaseModel):
    __tablename__ = "company_profiles"
    
    company_name = Column(String(200), default="Hamza Travels & Tours")
    phone = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    address = Column(String(300), nullable=True)
    logo_data = Column(LargeBinary, nullable=True)
    ntn = Column(String(50), nullable=True)
    strn = Column(String(50), nullable=True)
    website = Column(String(100), nullable=True)
