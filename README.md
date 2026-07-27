# PayFlow

A subscription billing demo showcasing Stripe payment integration, built with 
FastAPI, PostgreSQL, React + TypeScript, and deployed via Docker/Railway.

## Status: 🚧 In development

## Tech Stack
- Backend: FastAPI, SQLAlchemy, PostgreSQL, Alembic
- Payments: Stripe (Checkout, Subscriptions, Webhooks)
- Frontend: React, TypeScript, Vite
- Infra: Docker Compose, Railway

## Setup
See `.env.example` for required environment variables.

### Docker Compose (backend + frontend + Postgres)

```bash
cp .env.example .env   # fill in Stripe keys, etc.
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8000 (`/health` for a liveness check)
- Postgres: localhost:5432 (`payflow`/`payflow`/`payflow`)

### Backend (without Docker)

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # DATABASE_URL defaults to localhost:5432
alembic upgrade head   # apply migrations (requires Postgres running)
uvicorn app.main:app --reload
```

New migrations: `alembic revision --autogenerate -m "description"`, then review the generated file before applying.

### Frontend

```bash
cd frontend
npm install && npm run dev
```

Copy `frontend/.env.example` to `frontend/.env` and set `VITE_API_URL` to point at the backend (defaults to `http://localhost:8000`).
