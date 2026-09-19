# YourMarket

A **Django REST backend that reconciles cash-on-delivery (COD) orders for a small online shop.** It pulls every shipment, delivery status and payment settlement from the courier's customer-portal API (MNP Courier), stores them in PostgreSQL, works out how much each product really earned after wholesale cost, ads and courier charges, and e-mails a summary report.

The shop sells home-organisation products (shoe racks, garment-hanger stands …); the app replaces the manual spreadsheet work of matching "what was booked", "what was delivered / returned" and "what the courier actually paid out".

## What it does

1. **Sync** — for a date range, calls the courier portal's reports (booking summary, customer/consignee profile, QSR report, payment-instrument report, consignment details) and **upserts** them into the database (`update_or_create`, so re-running is safe).
2. **Link the data** — each consignment is tied to its **product** (by product description) and to its **payment settlement** (by payment id).
3. **Profit report** — `/customer/qsr/<ads>/<dc>/` totals the sale value of delivered orders, subtracts wholesale cost, ad spend and M&P charges, and returns/emails the net result per product.
4. **Alerts** — e-mails when a report can't be generated and a digest of shipments that need attention.
5. **Monthly automation** — a management command (`qsr_monthly`) walks through a month range and triggers the sync for each month.

## Architecture

```
Courier customer-portal API (bookings, QSR, payments, consignee, CN details)
                │  requests (API key header)
                ▼
     customer/views.py  ──►  Customer_DataAPIView   GET /customer/cm_data/<start>/<end>/<month>/
                │                    │ update_or_create
                ▼                    ▼
   PostgreSQL  ◄──  models: Product_details · PaymentDetails · Customer_Details · Email
                │
                ▼
     QSR_View  GET /customer/qsr/<ads>/<dc>/  ──►  profit per product ──► email (smtplib, Gmail SMTP)

manage.py qsr_monthly ──► customer/Jobs/qsr_job.py ──► calls /customer/cm_data/... month by month
```

| Path | Role |
|---|---|
| `yourmarket/` | Django project (settings, urls, `helpers.py`, and `authenticate_code.py` — a time-based hash check for requests that is currently switched off in the views) |
| `customer/models.py` | `Product_details`, `PaymentDetails`, `Customer_Details` (consignment), `Email` (dedup of sent alerts) |
| `customer/views.py` | The two API views described above |
| `customer/functions.py` | SMTP e-mail sending, report body builders, local-server start/health helpers |
| `customer/constants.py` | The product catalogue names used for reporting |
| `customer/Jobs/qsr_job.py`, `customer/management/commands/qsr_monthly.py` | Monthly sync job |

## API

| Method & path | Purpose |
|---|---|
| `GET /customer/cm_data/<start_date>/<end_date>/<month>/` | Pull reports from the courier for the period and store/update them |
| `GET /customer/qsr/<ads>/<dc>/` | Build the profit report; `ads` = ad expense, `dc` = M&P charges for the period; also e-mails it |
| `/admin/` | Django admin |

## Stack

- Python 3.9+, **Django 4.1**, **Django REST Framework** (JWT packages included)
- **PostgreSQL** (`psycopg2`)
- `requests` for the courier API, `smtplib` for e-mail, WhiteNoise for static files

## Setup

```bash
git clone https://github.com/SanaAkram/YourMarket.git
cd YourMarket

python -m venv .venv
# Windows:      .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate

pip install -r requirements.txt
```

### Configuration

The database, e-mail account and courier credentials are defined in `yourmarket/settings.py` and `customer/views.py`. **Replace them with your own values and keep them out of git** — ideally read them from environment variables:

```bash
# database (PostgreSQL)
DB_NAME=yourmarket
DB_USER=<postgres user>
DB_PASSWORD=<postgres password>
DB_HOST=localhost
DB_PORT=5433            # the project's default; use 5432 for a stock Postgres

# outgoing e-mail (Gmail SMTP with an app password)
DEFAULT_FROM_EMAIL=<sender address>
EMAIL_HOST_PASSWORD=<gmail app password>
EMAIL_TO=<where reports are sent>

# courier customer-portal API
COURIER_API_KEY=<key from the portal>
COURIER_ACCOUNT=<account code>
COURIER_LOCATION_ID=<location id>
```

Example of wiring the database to the environment in `settings.py`:

```python
import os

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "yourmarket"),
        "USER": os.environ["DB_USER"],
        "PASSWORD": os.environ["DB_PASSWORD"],
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5433"),
    }
}
```

Create the database and tables:

```sql
CREATE DATABASE yourmarket;
```

```bash
python manage.py migrate
python manage.py createsuperuser        # optional, for /admin/
```

## Run

```bash
python manage.py runserver

# sync one period, then request the profit report
curl http://127.0.0.1:8000/customer/cm_data/2024-01-01/2024-01-31/January/
curl http://127.0.0.1:8000/customer/qsr/15000/4000/

# or sync month by month with the management command
python manage.py qsr_monthly
```

## Notes

- Development settings are on (`DEBUG = True`, console e-mail backend option, permissive API permissions). Lock these down and set `ALLOWED_HOSTS` before deploying.
- The courier API is a third-party service used with the shop's own account; its report formats may change.
