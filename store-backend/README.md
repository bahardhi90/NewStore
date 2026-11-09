# Store Backend (Django + DRF)

API for a Persian men's fashion store. Django 5.2, DRF, PostgreSQL, Redis, Celery, JWT (phone + SMS OTP), Zarinpal.
API contract: [`contract/openapi.yaml`](contract/openapi.yaml) — shared with the Next.js frontend.

## Quick start with Docker (recommended)

```bash
cp .env.example .env
docker compose up -d --build                      # db, redis, web, celery, beat
docker compose exec web python manage.py seed_demo          # demo products, stores, shipping methods
docker compose exec web python manage.py createsuperuser    # phone + password for /admin/
```

- API: http://localhost:8000/api/
- Swagger UI: http://localhost:8000/api/docs/ (ReDoc: `/api/redoc/`, raw schema: `/api/schema/`)
- Admin: http://localhost:8000/admin/
- Health: http://localhost:8000/api/health/

In development the OTP code is printed in the logs: `docker compose logs -f celery web`.

## Run without Docker (Postgres + Redis still via Docker)

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements/dev.txt
cp .env.example .env
docker compose up -d db redis
python manage.py migrate
python manage.py seed_demo
python manage.py createsuperuser
python manage.py runserver
celery -A config worker -l info          # second terminal (Windows: add --pool=solo)
celery -A config beat -l info            # third terminal (auto-cancels unpaid orders)
```

Tip: for a quick local try without Celery, set `CELERY_TASK_ALWAYS_EAGER=True` in `.env` (tasks then run inline).

## Tests & quality

```bash
pytest                                    # uses SQLite in memory (config.settings.test)
pytest --cov=apps --cov-report=term-missing
black . && isort . && flake8
pre-commit install
python manage.py spectacular --file schema.yaml --validate
```

66 tests cover pricing, filters, query counts, OTP (expiry, wrong code, max attempts, throttling), cart (stock, merge),
checkout (stock reservation, snapshots, auto-cancel) and payments (success, cancel, failure, idempotency, gateway down).

## Try the flow with curl

```bash
curl -X POST localhost:8000/api/auth/otp/request/ -H 'Content-Type: application/json' -d '{"phone":"09121234567"}'
# read the code from the logs
curl -X POST localhost:8000/api/auth/otp/verify/ -H 'Content-Type: application/json' -d '{"phone":"09121234567","code":"12345"}'
TOKEN=<access>
curl localhost:8000/api/products/?category=jackets&on_sale=true
curl -X POST localhost:8000/api/cart/items/ -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{"variant_id":1,"quantity":1}'
```

## Project layout

```
config/            settings (base/dev/prod/test), urls, celery
apps/core          base model, pagination, error format, pricing, Persian messages, health
apps/accounts      User (phone login), OTP service, addresses, /me
apps/notifications SMS settings (Melipayamak), automatic messages per event, SMS log
apps/catalog       categories, collections, products, variants, images, filters, seed_demo
apps/cart          server cart + guest-cart merge
apps/orders        checkout (atomic + select_for_update), shipping methods, auto-cancel task, admin CSV export
apps/payments      Payment + PaymentMethod models, gateways (fake, zarinpal, digipay, snapppay), idempotent verify
apps/stores        store locations
apps/content       home banners + /home/ aggregate (cached), site name and logo
```

Business logic lives in `services.py` / `otp.py`; views only validate input and call services.

## Key behaviour

- **Prices:** `final_price = base × (100 − discount) / 100`, rounded down to 1,000 Toman (`apps/core/pricing.py`). Clients never send prices.
- **Errors:** always `{"detail": "...", "code": "...", "errors": {field: [...]}}`.
- **OTP:** 5 digits, hashed in Redis, 120 s TTL, 120 s resend cooldown, 5 attempts, hourly limits per phone and per IP.
- **Checkout:** locks variants, re-checks stock, snapshots items/prices/address, reserves stock, empties the cart.
  Unpaid orders are cancelled after `ORDER_PAYMENT_TIMEOUT_MINUTES` and stock is released.
- **Payment:** the gateway returns the browser to `${FRONTEND_URL}/payment/result`; the frontend calls `/api/payments/verify/`.
  Verification is idempotent and checks the amount. Zarinpal receives Rial (Toman × 10).
- **Payment methods (no technical access needed):** Admin → "روش‌های پرداخت". Tick "فعال" to show a method at checkout,
  untick to hide it. Connection details (Digipay, SnappPay, Zarinpal) are entered there, and a method can't be enabled
  until they are complete. Secrets are stored unencrypted in the database, so limit who gets admin access and protect backups.
- **Installments:** Digipay and SnappPay POST the browser back, so their callback is the frontend route
  `/api/payments/callback`, which redirects to `/payment/result`. Digipay credit/BNPL purchases are reported as delivered
  right after verification; SnappPay is verified and settled in the same step.
- **Site name and logo:** Admin → "تنظیمات سایت". The site name shows until a logo is uploaded; changes appear within a minute.
- **SMS (Melipayamak, no technical access needed):** Admin → "تنظیمات پیامک" picks the service (test mode only writes
  messages to the server log) and holds the Melipayamak username and password/API key. Admin → "پیامک‌های خودکار" has one
  message per event (login code, welcome, order paid/shipped/delivered/cancelled): write the text with named variables such as
  `{name}`, register the shown numbered version in the Melipayamak panel as a pattern, then enter its code (bodyId) and tick
  "فعال". Every message sent or failed is listed in "گزارش پیامک‌ها".

## Production

```bash
cp .env.example .env    # set DEBUG=False, SECRET_KEY, ALLOWED_HOSTS, FRONTEND_URL, POSTGRES_* , gateway keys
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

Migrations and `collectstatic` run automatically on start. Put HTTPS in front of the Nginx container.
Backups: `scripts/backup_db.sh` (cron daily, 14-day retention, restore command inside the script).
CI: `.github/workflows/ci.yml` (lint, migrations check, tests ≥ 80% coverage, schema validation).
Staging deploy on merge to `main`: `.github/workflows/deploy-staging.yml` (set the SSH secrets).
