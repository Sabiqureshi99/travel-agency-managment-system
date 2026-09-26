"""
TAMS — Quick Start Guide
========================

## Prerequisites

1. Python 3.12+
2. PostgreSQL 15+ (or use SQLite fallback)

## Setup Instructions

### Step 1: Create a virtual environment

```bash
python -m venv venv
venv\\Scripts\\activate     # Windows
```

### Step 2: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Configure the environment

```bash
copy .env.example .env
# Edit .env with your database credentials
```

### Step 4: Initialize the database

```bash
python setup_initial_data.py
```

This creates:
- All database tables
- Default admin account (username: admin, password: admin123)
- Default Chart of Accounts
- Required directories

### Step 5: Launch TAMS

```bash
python main.py
```

### Default Login

- **Username:** admin
- **Password:** admin123

> ⚠️ Change the admin password immediately after first login via Settings → Users.

---

## SQLite Fallback (No PostgreSQL)

If you don't have PostgreSQL installed, set in `.env`:

```
USE_SQLITE_FALLBACK=true
```

The application will use a local SQLite file at `data/hamza_travels.db`.

---

## Project Structure

```
TAMS/
├── main.py                # Entry point
├── setup_initial_data.py  # First-run setup
├── requirements.txt
├── .env.example
├── config/                # Database & settings
├── core/                  # Base classes
├── models/                # Database models (14 files)
├── repositories/          # Data access layer
├── services/              # Business logic (14 files)
├── viewmodels/            # MVVM view models
├── ui/                    # All UI code
│   ├── styles/            # QSS themes
│   ├── windows/           # Main windows
│   ├── widgets/           # Reusable widgets
│   └── pages/             # Module pages (15 modules)
├── reports/               # PDF & Excel generators
├── utils/                 # Utilities
├── alembic/               # DB migrations
├── assets/                # Icons, images, fonts
├── backups/               # Database backups (auto-created)
├── logs/                  # Application logs (auto-created)
└── documents/             # Uploaded documents (auto-created)
```

---

## Modules

| Module | Description |
|--------|-------------|
| Dashboard | Sales stats, charts, today's activities |
| Customers | Full CRM with passport/visa tracking |
| Employees | HR with attendance, salary, permissions |
| Flights | Domestic & international ticket booking |
| Visa | Full visa application workflow |
| Umrah | Package management + pilgrim tracking |
| Hajj | Group-based Hajj management |
| Hotels | Hotel database + booking + vouchers |
| Tours | Package tours (domestic + international) |
| Transport | Vehicles, drivers, bookings, maintenance |
| Suppliers | Airline, hotel, visa, transport suppliers |
| Accounting | Double-entry bookkeeping, P&L, invoices |
| Reports | Comprehensive sales, customer, visa reports |
| Documents | Centralized document storage |
| Settings | Company, users, backup, theme settings |

---

## Support

**Company:** Hamza Travels & Tours  
**Email:** info@hamzatravels.com
"""
