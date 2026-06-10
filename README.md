# Finance Tracker

A personal finance management web application built with Django. Track income,
expenses, and transfers across multiple bank accounts, visualize your spending
with interactive dashboards, generate detailed reports, and import/export your
data — all from a clean Bootstrap-based interface.

> Currency defaults to Indian Rupee (₹) and the timezone to `Asia/Kolkata`.
> Both can be changed in `finance_tracker/settings.py`.

## Features

- **Dashboard** — Monthly summary cards (income, expense, savings, total
  balance), month-over-month comparison, and interactive charts: expense
  category pie, 6-month income/expense/savings trend, 30-day daily expense
  trend, and account balance distribution.
- **Transactions** — Record **income**, **expenses**, and **transfers** between
  accounts. Account balances update automatically on create, edit, and delete.
  Browse all transactions with search, type/category/account filters, date-range
  filtering, and pagination.
- **Accounts** — Manage multiple bank accounts (savings, current, salary, cash,
  credit card, UPI wallet, investment, etc.), each with its own color, icon, and
  running balance. View per-account detail with recent transactions and totals.
- **Categories** — Create custom income and expense categories with colors and
  Bootstrap icons.
- **Reports** — Monthly, category-wise, account-wise, and annual reports with
  charts and breakdowns. Export any monthly report to Excel.
- **Import / Export** — Export all transactions to Excel (`.xlsx`) or CSV,
  import transactions from Excel, and back up / restore the full SQLite database.
- **Sample data** — Seed the app with example accounts, categories, and ~3
  months of transactions for a quick demo.

## Tech Stack

- **Backend:** Django 4.2
- **Database:** SQLite
- **Frontend:** Django templates, Bootstrap, Bootstrap Icons, HTMX (for partial
  page updates), Chart.js (for visualizations)
- **Data:** openpyxl & pandas (Excel), django-import-export, python-dateutil

## Project Structure

```
finance_tracker/
├── finance_tracker/   # Project settings, root URLs, WSGI
├── accounts/          # Bank accounts (CRUD, detail, JSON API)
├── transactions/      # Income/expense/transfer, categories, import/export
│   └── services.py    # Aggregation helpers for dashboard & reports
├── dashboard/         # Main dashboard view & charts
├── reports/           # Monthly / category / account / annual reports
├── settings_app/      # Settings page, seed data, clear data
├── templates/         # Shared and per-app templates
├── manage.py
└── requirements.txt
```

## Getting Started

### Prerequisites

- Python 3.10+

### Installation

```bash
# 1. (Recommended) create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Apply database migrations
python manage.py migrate

# 4. (Optional) create an admin user for the Django admin
python manage.py createsuperuser

# 5. Run the development server
python manage.py runserver
```

Then open <http://127.0.0.1:8000/> in your browser. The Django admin is
available at <http://127.0.0.1:8000/admin/>.

To populate the app with demo data, go to **Settings** and use the
"Seed sample data" action.

## URL Overview

| Path                      | Description                              |
| ------------------------- | ---------------------------------------- |
| `/`                       | Dashboard                                |
| `/accounts/`              | Account list & management                |
| `/transactions/expense/`  | Add an expense                           |
| `/transactions/income/`   | Add income                               |
| `/transactions/transfer/` | Transfer between accounts                |
| `/transactions/list/`     | All transactions (search & filter)       |
| `/transactions/categories/` | Manage categories                      |
| `/transactions/import-export/` | Import, export, backup & restore    |
| `/reports/`               | Reports (monthly / category / account / annual) |
| `/settings/`              | Settings, seed & clear data              |
| `/admin/`                 | Django admin                             |

## Configuration

Key settings live in `finance_tracker/settings.py`:

- `DEFAULT_CURRENCY` / `DEFAULT_CURRENCY_CODE` — currency symbol and code (₹ / INR)
- `TIME_ZONE` — defaults to `Asia/Kolkata`
- `DATABASES` — SQLite by default (`db.sqlite3`)

> **Security note:** `SECRET_KEY` and `DEBUG = True` in `settings.py` are set for
> local development only. Set a fresh secret key, disable debug, and configure
> `ALLOWED_HOSTS` before deploying to production.

## License

This project is provided as-is for personal use. Add a license of your choice.
