"""
Fix missing columns in both the dev and dist databases.
Applies any missing columns that exist in models but not in the DB.
"""
import sqlite3
import os

DBS = [
    r'data\hamza_travels.db',
    r'dist\TAMS\data\hamza_travels.db',
]

# Columns to add: (table, column_name, column_definition)
MISSING_COLUMNS = [
    ('custom_umrah_bookings', 'base_purchase_cost', 'FLOAT DEFAULT 0.0'),
    ('custom_umrah_bookings', 'profit_margin', 'FLOAT DEFAULT 0.0'),
]

for db_path in DBS:
    if not os.path.exists(db_path):
        print(f'SKIP (not found): {db_path}')
        continue

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    for table, col, col_def in MISSING_COLUMNS:
        cur.execute(f'PRAGMA table_info({table})')
        existing_cols = [r[1] for r in cur.fetchall()]

        if col not in existing_cols:
            cur.execute(f'ALTER TABLE {table} ADD COLUMN {col} {col_def}')
            print(f'[{db_path}] Added column: {table}.{col}')
        else:
            print(f'[{db_path}] Column already exists: {table}.{col}')

    conn.commit()
    conn.close()

print('\nDone! All missing columns have been applied.')
