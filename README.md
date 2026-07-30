# PayFlow

A subscription billing demo: register, pick a plan, pay through Stripe Checkout, and
manage your subscription from a dashboard — with the subscription state kept in sync
by Stripe webhooks rather than trusted client-side.

## Live demo

- **App:** https://frontend-production-f71e.up.railway.app
- **API docs:** https://backend-production-69e3.up.railway.app/docs

Stripe is in **test/sandbox mode** — no real charges. Use test card `4242 4242 4242 4242`,
any future expiry date, any CVC, and any ZIP to complete checkout.

## Tech stack

- **Backend:** FastAPI, SQLAlchemy (async), PostgreSQL, Alembic
- **Payments:** Stripe (Checkout Sessions, Subscriptions, Webhooks)
- **Frontend:** React, TypeScript, Vite, TanStack Query
- **Infra:** Docker, Docker Compose, Railway

## Features

- Email/password registration and login (JWT bearer auth)
- Plan selection (Basic / Pro) fetched from the database, priced in Stripe
- Stripe Checkout for subscribing
- Subscription status dashboard (plan, status, renewal date)
- Cancel subscription (takes effect at the end of the current billing period)
- Webhook-driven sync: subscription state is written by Stripe webhook events
  (`checkout.session.completed`, `customer.subscription.updated/.deleted`), not by the
  client, so it stays correct even if a user closes the tab mid-checkout

## Architecture notes

- **Migrations run automatically on container start.** The backend's entrypoint script
  runs `alembic upgrade head` before starting uvicorn, and exits loudly (non-zero,
  full traceback) if migrations fail rather than serving against a broken schema.
- **Webhook handling is idempotent.** `POST /webhooks/stripe` verifies the Stripe
  signature, then upserts by `stripe_subscription_id` — replayed or out-of-order
  events converge to the same state instead of creating duplicates.
- **JWT auth**, bcrypt-hashed passwords, stateless bearer tokens validated per-request
  against the signing secret.

## Run it locally

Requires Docker.

```bash
cp .env.example .env   # fill in your own Stripe test-mode keys
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8000 (`/health` for a liveness check, `/docs` for the API)
- Postgres: localhost:5432 (`payflow`/`payflow`/`payflow`)

Migrations run automatically on backend startup. Plan seeding is a separate one-time
step — after the first successful `docker compose up`, seed the Basic/Pro plans with:

```bash
docker compose exec backend python -m app.scripts.seed_plans
```

### Environment variables

See `.env.example` for the full list. You'll need your own Stripe test-mode keys from
the [Stripe dashboard](https://dashboard.stripe.com/test/apikeys), plus Price IDs for
two test products (Basic and Pro).

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Postgres connection string |
| `STRIPE_SECRET_KEY` / `STRIPE_PUBLISHABLE_KEY` | Stripe API keys (test mode) |
| `STRIPE_WEBHOOK_SECRET` | Signing secret for `/webhooks/stripe` (from `stripe listen` locally, or a dashboard-configured endpoint in production) |
| `STRIPE_PRICE_BASIC` / `STRIPE_PRICE_PRO` | Stripe Price (or Product) IDs seeded into the `plans` table |
| `JWT_SECRET_KEY` | Signs auth tokens — use a real random value outside local dev |
| `FRONTEND_URL` | Used for CORS and Stripe Checkout success/cancel redirects |

### Running backend or frontend without Docker

```bash
# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # DATABASE_URL defaults to localhost:5432
alembic upgrade head    # requires Postgres running
uvicorn app.main:app --reload

# Frontend
cd frontend
cp .env.example .env   # VITE_API_URL defaults to http://localhost:8000
npm install && npm run dev
```

New migrations: `alembic revision --autogenerate -m "description"`, then review the
generated file before applying.
