"""
setup_initial_data.py
=====================
First-run initialisation script for TAMS.

Run this ONCE after setting up the database:
    python setup_initial_data.py

This will:
1. Create all database tables
2. Set up the default Chart of Accounts (Pakistan standard)
3. Create the Admin user
4. Create default employee permissions
"""
import sys
import os
from pathlib import Path

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env", override=False)

from utils.logger import setup_logging
setup_logging()

import logging
logger = logging.getLogger(__name__)


def main() -> None:
    """Run all first-run setup steps."""
    print("=" * 60)
    print("  Hamza Travels & Tours — TAMS First-Run Setup")
    print("=" * 60)

    # Step 1: Init database
    print("\n[1/5] Initialising database...")
    from config.database import init_database
    if not init_database():
        print("❌ Database initialisation failed. Check your .env settings.")
        sys.exit(1)
    print("✅ Database ready.")

    # Step 2: Create all tables
    print("\n[2/5] Creating database tables...")
    from config.database import _get_engine
    from core.base_model import Base
    import models  # noqa: F401
    Base.metadata.create_all(_get_engine())
    print("✅ All tables created.")

    # Step 3: Create admin user
    print("\n[3/5] Creating admin user...")
    _create_admin_user()

    # Step 4: Set up Chart of Accounts
    print("\n[4/5] Setting up Chart of Accounts...")
    _setup_chart_of_accounts()

    # Step 5: Create settings record
    print("\n[5/5] Finalising setup...")
    print("✅ Setup complete!")
    print("\n" + "=" * 60)
    print("  You can now launch TAMS by running: python main.py")
    print("  Default login: admin / admin123")
    print("  ⚠️  Please change the admin password after first login!")
    print("=" * 60)


def _create_admin_user() -> None:
    """Create the default admin user if it doesn't exist."""
    from config.database import get_session
    from models.user import User
    from core.enums import UserRole, UserStatus
    from core.permissions import ADMIN_PERMISSIONS
    from utils.encryption import hash_password
    from core.base_model import generate_uuid
    from sqlalchemy import select
    from datetime import datetime, timezone

    with get_session() as session:
        existing = session.execute(
            select(User).where(User.username == "admin")
        ).scalar_one_or_none()

        if existing:
            print("  ⚠️  Admin user already exists. Skipping.")
            return

        admin = User()
        admin.id = generate_uuid()
        admin.username = "admin"
        admin.password_hash = hash_password("admin123")
        admin.full_name = "System Administrator"
        admin.email = "admin@hamzatravels.com"
        admin.role = UserRole.ADMIN.value
        admin.status = UserStatus.ACTIVE.value
        admin.permissions = ADMIN_PERMISSIONS
        admin.failed_login_attempts = 0
        admin.created_at = datetime.now(timezone.utc)
        admin.updated_at = datetime.now(timezone.utc)
        admin.is_deleted = False

        session.add(admin)
        print("  ✅ Admin user created. Username: admin | Password: admin123")


def _setup_chart_of_accounts() -> None:
    """Create a standard Pakistan-appropriate Chart of Accounts."""
    from config.database import get_session
    from models.accounting import ChartOfAccount
    from core.base_model import generate_uuid
    from datetime import datetime, timezone
    from sqlalchemy import select

    accounts = [
        # Assets
        ("1000", "Assets", "Asset", None, False),
        ("1100", "Current Assets", "Asset", "1000", False),
        ("1110", "Cash in Hand", "Asset", "1100", True, True),
        ("1120", "Bank Accounts", "Asset", "1100", False),
        ("1121", "Main Bank Account", "Asset", "1120", True, False, True),
        ("1130", "Accounts Receivable", "Asset", "1100", True),
        ("1200", "Fixed Assets", "Asset", "1000", False),
        ("1210", "Office Equipment", "Asset", "1200", True),
        ("1220", "Furniture & Fixtures", "Asset", "1200", True),

        # Liabilities
        ("2000", "Liabilities", "Liability", None, False),
        ("2100", "Current Liabilities", "Liability", "2000", False),
        ("2110", "Accounts Payable", "Liability", "2100", True),
        ("2120", "Customer Advances", "Liability", "2100", True),
        ("2130", "Tax Payable", "Liability", "2100", True),

        # Equity
        ("3000", "Equity", "Equity", None, False),
        ("3100", "Owner Equity", "Equity", "3000", True),
        ("3200", "Retained Earnings", "Equity", "3000", True),

        # Income
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

        # Expenses
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
        # Build a code -> id map for parent lookups
        code_to_id: dict[str, str] = {}

        for acc_data in accounts:
            code, name, acc_type, parent_code = acc_data[0], acc_data[1], acc_data[2], acc_data[3]
            is_leaf = acc_data[4] if len(acc_data) > 4 else True
            is_bank = acc_data[6] if len(acc_data) > 6 else False

            # Check if already exists
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
            acc.is_bank_account = is_bank
            acc.currency = "PKR"
            acc.opening_balance = 0
            acc.status = "Active"
            acc.created_at = datetime.now(timezone.utc)
            acc.updated_at = datetime.now(timezone.utc)
            acc.is_deleted = False

            session.add(acc)
            session.flush()
            code_to_id[code] = acc.id

        print(f"  ✅ Chart of Accounts set up with {len(accounts)} accounts.")


if __name__ == "__main__":
    main()
