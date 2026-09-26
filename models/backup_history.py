import enum
from sqlalchemy import Column, String, DateTime, Enum
from core.base_model import BaseModel

class BackupType(enum.Enum):
    FULL = "FULL"
    INCREMENTAL = "INCREMENTAL"

class BackupHistory(BaseModel):
    __tablename__ = 'backup_history'
    
    backup_type = Column(Enum(BackupType), default=BackupType.INCREMENTAL, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    file_path = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False) # e.g. "SUCCESS", "FAILED"
