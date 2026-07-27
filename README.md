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

### Frontend

```bash
cd frontend
npm install && npm run dev
```

Copy `frontend/.env.example` to `frontend/.env` and set `VITE_API_URL` to point at the backend (defaults to `http://localhost:8000`).
