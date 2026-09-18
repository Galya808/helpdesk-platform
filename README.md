# Helpdesk Platform

Helpdesk platform built with FastAPI, PostgreSQL and Next.js.

## Applications

- `backend` — FastAPI API, PostgreSQL persistence, migrations, metrics, and tests
- `frontend` — lightweight Next.js interface for all role-based API workflows

## Run locally

Start the database and API:

```bash
docker compose up -d --build
```

In another terminal, start the frontend:

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open `http://localhost:3000`.

## Local database

Start PostgreSQL:

```bash
docker compose up -d db
```

Check the service status:

```bash
docker compose ps
```

View database logs:

```bash
docker compose logs db
```

Connect with psql:

```bash
docker compose exec db psql -U helpdesk -d helpdesk
```

Stop the services:

```bash
docker compose down
```
