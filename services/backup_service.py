import os
import json
import gzip
import shutil
import logging
import sqlite3
import logging
from datetime import datetime, timezone
from sqlalchemy import select
from core.base_service import BaseService
from core.base_model import Base
from models.backup_history import BackupHistory, BackupType

logger = logging.getLogger(__name__)

class BackupServiceError(Exception):
    """Custom exception for Backup service errors."""
    pass

class BackupService(BaseService):
    """
    Service for creating and managing incremental JSON backups.
    """
    
    def __init__(self, backup_dir: str = "backups") -> None:
        super().__init__()
        self.backup_dir = backup_dir
        logger.info(f"BackupService initialized with directory: {backup_dir}")
        self._ensure_backup_directory()

    def _ensure_backup_directory(self) -> None:
        """Ensure the backup directory exists."""
        try:
            os.makedirs(self.backup_dir, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create backup directory {self.backup_dir}: {e}")
            raise BackupServiceError(f"Initialization failed: {e}") from e

    def get_backup_history(self):
        with self._get_session() as session:
            return session.query(BackupHistory).order_by(BackupHistory.timestamp.desc()).all()

    def create_incremental_backup(self) -> str:
        """
        Creates an incremental backup by querying records updated since the last backup.
        """
        logger.info("Starting incremental backup...")
        try:
            with self._get_session() as session:
                # 1. Find last backup timestamp
                last_backup = session.query(BackupHistory).filter(BackupHistory.status == "SUCCESS").order_by(BackupHistory.timestamp.desc()).first()
                last_timestamp = last_backup.timestamp if last_backup else datetime(1970, 1, 1, tzinfo=timezone.utc)
                
                is_full = last_backup is None
                
                backup_data = {}
                record_count = 0
                
                # 2. Iterate all mapped models
                for mapper in Base.registry.mappers:
                    model_class = mapper.class_
                    
                    # Ensure the model has updated_at
                    if not hasattr(model_class, 'updated_at'):
                        continue
                        
                    table_name = model_class.__tablename__
                    
                    # Query updated records
                    records = session.query(model_class).filter(model_class.updated_at > last_timestamp).all()
                    
                    if records:
                        def _to_dict(r):
                            if hasattr(r, 'to_dict'):
                                return r.to_dict()
                            res = {}
                            for col in r.__table__.columns:
                                v = getattr(r, col.name)
                                if isinstance(v, datetime):
                                    v = v.isoformat()
                                res[col.name] = v
                            return res
                        
                        backup_data[table_name] = [_to_dict(r) for r in records]
                        record_count += len(records)
                
                if record_count == 0:
                    logger.info("No new records to backup.")
                    raise BackupServiceError("No new records to backup since the last run.")
                
                # 3. Serialize and Compress
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"backup_{'full' if is_full else 'inc'}_{timestamp_str}.json.gz"
                backup_path = os.path.join(self.backup_dir, backup_name)
                
                json_str = json.dumps(backup_data, default=str)
                with gzip.open(backup_path, 'wt', encoding='utf-8') as f:
                    f.write(json_str)
                
                # 4. Log in BackupHistory
                history = BackupHistory(
                    backup_type=BackupType.FULL if is_full else BackupType.INCREMENTAL,
                    timestamp=datetime.now(timezone.utc),
                    file_path=backup_path,
                    status="SUCCESS"
                )
                session.add(history)
                session.commit()
                return backup_path
        except Exception as e:
            logger.error(f"Incremental backup failed: {e}")
            raise BackupServiceError(f"Backup failed: {e}") from e

    def create_full_sqlite_backup(self) -> str:
        """
        Creates a full physical backup of the SQLite database file.
        """
        logger.info("Starting full SQLite physical backup...")
        try:
            from config.database import get_db_path
            db_path = get_db_path()
            if not os.path.exists(db_path):
                raise BackupServiceError(f"Source database file not found: {db_path}")

            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"hamza_travels_full_backup_{timestamp_str}.db"
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            # Safe physical backup using native SQLite backup API (handles WAL files correctly)
            src = sqlite3.connect(db_path)
            dst = sqlite3.connect(backup_path)
            with dst:
                src.backup(dst)
            dst.close()
            src.close()
            
            with self._get_session() as session:
                history = BackupHistory(
                    backup_type=BackupType.FULL,
                    timestamp=datetime.now(timezone.utc),
                    file_path=backup_path,
                    status="SUCCESS"
                )
                session.add(history)
                session.commit()
                
            return backup_path
        except Exception as e:
            logger.error(f"Full SQLite backup failed: {e}")
            raise BackupServiceError(f"Backup failed: {e}") from e


    def restore_from_backup(self, file_path: str) -> None:
        """
        Restores data from a gzipped JSON backup file using UPSERT (session.merge).
        """
        logger.info(f"Starting restore from {file_path}...")
        if not os.path.exists(file_path):
            raise BackupServiceError(f"Backup file not found: {file_path}")
            
        if file_path.endswith('.db'):
            # Full SQLite Database Restore
            try:
                from config.database import get_db_path, _engine
                db_path = get_db_path()
                
                # Dispose of SQLAlchemy connections so the database is not locked
                if _engine:
                    _engine.dispose()
                
                # Use native SQLite backup API in reverse to restore
                src = sqlite3.connect(file_path)
                dst = sqlite3.connect(db_path)
                with dst:
                    src.backup(dst)
                dst.close()
                src.close()
                logger.info("Successfully restored SQLite .db backup.")
                return
            except Exception as e:
                logger.error(f"Failed to restore SQLite database: {e}")
                raise BackupServiceError(f"Database restore failed: {e}") from e
                
        try:
            # 1. Unzip and load JSON (Incremental / Legacy Backup)
            with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                backup_data = json.load(f)
                
            with self._get_session() as session:
                try:
                    # 2. Iterate through serialized records and Models
                    model_map = {mapper.class_.__tablename__: mapper.class_ for mapper in Base.registry.mappers}
                    
                    for table_name, records in backup_data.items():
                        if table_name not in model_map:
                            logger.warning(f"Table {table_name} not found in current schema. Skipping.")
                            continue
                            
                        model_class = model_map[table_name]
                        
                        for record_dict in records:
                            # 3. UPSERT using session.merge
                            # We instantiate the model without adding it to session directly,
                            # then merge it.
                            
                            # Convert datetime strings back to datetime objects if needed?
                            # SQLAlchemy merge handles kwargs well, but if there's type issues, we might need a parser.
                            # For now, let SQLAlchemy coerce types.
                            instance = model_class(**record_dict)
                            session.merge(instance)
                            
                    # Commit the huge transaction
                    session.commit()
                    logger.info("Successfully restored backup.")
                except Exception as db_e:
                    session.rollback()
                    logger.error(f"Database error during restore: {db_e}. Rolled back.")
                    raise BackupServiceError(f"Database restore failed: {db_e}") from db_e
                    
        except Exception as e:
            logger.error(f"Error reading backup file: {e}")
            raise BackupServiceError(f"Restore failed: {e}") from e
