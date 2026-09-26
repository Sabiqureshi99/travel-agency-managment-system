import sqlite3, os

db = r'dist\TAMS\data\hamza_travels.db'
print('DB exists:', os.path.exists(db))
conn = sqlite3.connect(db)
cur = conn.cursor()

# List all tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cur.fetchall()]
print(f'Tables ({len(tables)}): {tables}')

# Check admin user
cur.execute("SELECT username, role, status FROM users WHERE username='admin'")
row = cur.fetchone()
print('Admin user:', row)

# Count rows in key tables
for t in ['users', 'customers', 'umrah_bookings', 'flight_bookings', 'accounting_entries']:
    if t in tables:
        cur.execute(f'SELECT COUNT(*) FROM {t}')
        print(f'  {t}: {cur.fetchone()[0]} rows')

conn.close()
print('DB check complete.')
