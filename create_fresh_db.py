"""
create_fresh_db.py
==================
Creates a brand new clean database with the full current schema
and only the admin user + chart of accounts. No test data.
Then copies it to dist/TAMS/data/
"""
import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Point to a fresh temp DB first
FRESH_DB = PROJECT_ROOT / "data" / "fresh_hamza_travels.db"
DIST_DB = PROJECT_ROOT / "dist" / "TAMS_ERP" / "data" / "hamza_travels.db"
DEV_DB = PROJECT_ROOT / "data" / "hamza_travels.db"

# Remove old fresh DB if exists
if FRESH_DB.exists():
    FRESH_DB.unlink()

# Set environment to use our fresh DB path
os.environ["USE_SQLITE_FALLBACK"] = "true"
os.environ["SQLITE_PATH"] = str(FRESH_DB)

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env", override=False)
os.environ["USE_SQLITE_FALLBACK"] = "true"

# Reset settings singleton so it picks up our env override
from config import settings as settings_module
settings_module.settings._load()

# Override the db path resolver to point to fresh DB
import config.database as db_module
db_module._engine = None
db_module._SessionLocal = None

# Monkey-patch get_db_path to return our fresh DB
db_module.get_db_path = lambda: str(FRESH_DB)

# Init database (creates all tables via Alembic)
print("Creating fresh database with full schema...")
from config.database import init_database, _get_engine
from core.base_model import Base
import models  # noqa: F401

Base.metadata.create_all(_get_engine())
print(f"Schema created at: {FRESH_DB}")

# Seed admin user
print("Creating admin user...")
from config.database import get_session
from models.user import User
from core.enums import UserRole, UserStatus
from core.permissions import ADMIN_PERMISSIONS
from utils.encryption import hash_password
from core.base_model import generate_uuid
from sqlalchemy import select
from datetime import datetime, timezone

with get_session() as session:
    existing_admin = session.execute(select(User).where(User.username == "sabiqureshi80@gmail.com")).scalar_one_or_none()
    if not existing_admin:
        admin = User()
        admin.id = generate_uuid()
        admin.username = "sabiqureshi80@gmail.com"
        admin.password_hash = hash_password("Sabiq12#")
        admin.full_name = "Sabiq Qureshi"
        admin.email = "Sabiqureshi80@gmail.com"
        admin.role = UserRole.ADMIN.value
        admin.status = UserStatus.ACTIVE.value
        admin.permissions = ADMIN_PERMISSIONS
        admin.failed_login_attempts = 0
        admin.created_at = datetime.now(timezone.utc)
        admin.updated_at = datetime.now(timezone.utc)
        admin.is_deleted = False
        session.add(admin)
        print("Admin user created: Sabiqureshi80@gmail.com / Sabiq12#")

    existing_owner = session.execute(select(User).where(User.username == "hamzairfantravel1@gmail.com")).scalar_one_or_none()
    if not existing_owner:
        from core.permissions import OWNER_PERMISSIONS
        owner = User()
        owner.id = generate_uuid()
        owner.username = "hamzairfantravel1@gmail.com"
        owner.password_hash = hash_password("Sabiq12#")
        owner.full_name = "Hamza Irfan"
        owner.email = "Hamzairfantravel1@gmail.com"
        owner.role = UserRole.OWNER.value
        owner.status = UserStatus.ACTIVE.value
        owner.permissions = OWNER_PERMISSIONS
        owner.failed_login_attempts = 0
        owner.created_at = datetime.now(timezone.utc)
        owner.updated_at = datetime.now(timezone.utc)
        owner.is_deleted = False
        session.add(owner)
        print("Owner user created: Hamzairfantravel1@gmail.com / Sabiq12#")

    # ── Seed Company Configuration ────────────────────────────────────────────────
    from models.company_profile import CompanyProfile
    existing_company = session.execute(select(CompanyProfile)).scalar_one_or_none()
    if not existing_company:
        company = CompanyProfile(
            id=generate_uuid(),
            company_name="Hamza Travels & Tours",
            email="Hamzairfantravel1@gmail.com",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            is_deleted=False
        )
        session.add(company)
        print("Default Company Profile created.")
        
    session.commit()

# Seed Chart of Accounts
print("Seeding Chart of Accounts...")
from models.accounting import ChartOfAccount

accounts = [
    ("1000", "Assets", "Asset", None, False),
    ("1100", "Current Assets", "Asset", "1000", False),
    ("1110", "Cash in Hand", "Asset", "1100", True),
    ("1120", "Bank Accounts", "Asset", "1100", False),
    ("1121", "Main Bank Account", "Asset", "1120", True),
    ("1130", "Accounts Receivable", "Asset", "1100", True),
    ("1200", "Fixed Assets", "Asset", "1000", False),
    ("1210", "Office Equipment", "Asset", "1200", True),
    ("1220", "Furniture & Fixtures", "Asset", "1200", True),
    ("2000", "Liabilities", "Liability", None, False),
    ("2100", "Current Liabilities", "Liability", "2000", False),
    ("2110", "Accounts Payable", "Liability", "2100", True),
    ("2120", "Customer Advances", "Liability", "2100", True),
    ("2130", "Tax Payable", "Liability", "2100", True),
    ("3000", "Equity", "Equity", None, False),
    ("3100", "Owner Equity", "Equity", "3000", True),
    ("3200", "Retained Earnings", "Equity", "3000", True),
    ("4000", "Income", "Income", None, False),
    ("4100", "Flight Ticket Income", "Income", "4000", True),
    ("4200", "Visa Processing Income", "Income", "4000", True),
    ("4300", "Umrah Package Income", "Income", "4000", True),
    ("4400", "Hajj Package Income", "Income", "4000", True),
    ("4500", "Hotel Booking Income", "Income", "4000", True),
    ("4600", "Tour Package Income", "Income", "4000", True),
    ("4700", "Transport Income", "Income", "4000", True),
    ("4800", "Other Income", "Income", "4000", True),
    ("4900", "Commission Income", "Income", "4000", True),
    ("5000", "Expenses", "Expense", None, False),
    ("5100", "Salaries & Wages", "Expense", "5000", True),
    ("5200", "Office Rent", "Expense", "5000", True),
    ("5300", "Utilities", "Expense", "5000", True),
    ("5400", "Marketing & Advertising", "Expense", "5000", True),
    ("5500", "Travel & Entertainment", "Expense", "5000", True),
    ("5600", "Office Supplies", "Expense", "5000", True),
    ("5700", "Communication", "Expense", "5000", True),
    ("5800", "Bank Charges", "Expense", "5000", True),
    ("5900", "Miscellaneous Expenses", "Expense", "5000", True),
]

with get_session() as session:
    code_to_id = {}
    for acc_data in accounts:
        code, name, acc_type, parent_code = acc_data[0], acc_data[1], acc_data[2], acc_data[3]
        is_leaf = acc_data[4] if len(acc_data) > 4 else True

        existing = session.execute(
            select(ChartOfAccount).where(ChartOfAccount.account_code == code)
        ).scalar_one_or_none()
        if existing:
            code_to_id[code] = existing.id
            continue

        acc = ChartOfAccount()
        acc.id = generate_uuid()
        acc.account_code = code
        acc.account_name = name
        acc.account_type = acc_type
        acc.parent_id = code_to_id.get(parent_code) if parent_code else None
        acc.is_leaf = is_leaf
        acc.is_bank_account = False
        acc.currency = "PKR"
        acc.opening_balance = 0
        acc.status = "Active"
        acc.created_at = datetime.now(timezone.utc)
        acc.updated_at = datetime.now(timezone.utc)
        acc.is_deleted = False
        session.add(acc)
        session.flush()
        code_to_id[code] = acc.id
    print(f"Chart of Accounts seeded with {len(accounts)} accounts.")

# Flush WAL to main DB so we don't lose data when copying
print("Checkpointing database WAL...")
from sqlalchemy import text
with _get_engine().connect() as conn:
    conn.execute(text("PRAGMA wal_checkpoint(TRUNCATE)"))

# Copy fresh DB to dist
import shutil
DIST_DB.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(str(FRESH_DB), str(DIST_DB))
print(f"\nClean database copied to: {DIST_DB}")
print("Admin Login: Sabiqureshi80@gmail.com / Sabiq12#")
print("Owner Login: Hamzairfantravel1@gmail.com / Sabiq12#")
print("Done!")
