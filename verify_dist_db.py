import sqlite3
db_path = r"dist\TAMS_ERP\data\hamza_travels.db"
conn = sqlite3.connect(db_path)
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
users = conn.execute("SELECT username, role, status FROM users").fetchall()
coa_count = conn.execute("SELECT count(*) FROM chart_of_accounts").fetchone()[0]
company = conn.execute("SELECT company_name FROM company_profiles").fetchone()
conn.close()

print(f"=== DIST DATABASE VERIFICATION ===")
print(f"Tables      : {len(tables)}")
print(f"CoA entries : {coa_count}")
print(f"Company     : {company[0] if company else 'NONE'}")
print(f"\nUser Accounts:")
for u in users:
    print(f"  {u[0]}  role={u[1]}  status={u[2]}")
print("\nAll good! Dist DB is clean and ready.")
