"""
migrate_age_column.py
=====================
Run this once when PostgreSQL is running to add the `age` column
to the `customer_family_members` table.

Usage:
    .\\venv\\Scripts\\python.exe migrate_age_column.py
"""
import sys
sys.path.insert(0, '.')

from config.database import _get_engine
from sqlalchemy import text

def run():
    engine = _get_engine()
    with engine.connect() as conn:
        # Adds the column only if it doesn't already exist (PostgreSQL 9.6+)
        conn.execute(text("""
            ALTER TABLE customer_family_members
            ADD COLUMN IF NOT EXISTS age INTEGER;
        """))
        conn.commit()
    print("✅ Migration complete: 'age' column added to customer_family_members")

if __name__ == "__main__":
    run()
