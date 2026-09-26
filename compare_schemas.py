import sqlite3

dev = sqlite3.connect('data/hamza_travels.db')
dist = sqlite3.connect('dist/TAMS/data/hamza_travels.db')

dev_tables = set(r[0] for r in dev.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())
dist_tables = set(r[0] for r in dist.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())

missing_tables = dev_tables - dist_tables
print('Tables missing from dist DB:', missing_tables)

for table in sorted(dev_tables & dist_tables):
    dev_cols = set(r[1] for r in dev.execute(f'PRAGMA table_info({table})').fetchall())
    dist_cols = set(r[1] for r in dist.execute(f'PRAGMA table_info({table})').fetchall())
    missing_cols = dev_cols - dist_cols
    if missing_cols:
        print(f'  {table}: missing columns {missing_cols}')

dev.close()
dist.close()
print('Schema comparison done.')
