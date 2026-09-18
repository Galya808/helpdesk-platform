# Helpdesk Platform Frontend

Lightweight Next.js interface for the Helpdesk Platform API.

## Requirements

- Node.js 20.9 or newer
- npm
- the backend running on port `8000`

## Installation

From the `frontend` directory:

```bash
npm install
cp .env.example .env.local
```

## Configuration

`NEXT_PUBLIC_API_URL` contains the public backend URL used by the browser.
The local default is `http://127.0.0.1:8000`.

Never store secrets in variables prefixed with `NEXT_PUBLIC_` because their
values are included in the browser bundle.

## Development

```bash
npm run dev
```

Open `http://localhost:3000`.

## Quality checks

```bash
npm run lint
npm run build
```

## Features

- backend health status
- customer registration and authentication
- role-aware navigation
- ticket creation, filtering, pagination, and detail views
- ticket comments
- support-agent assignment, status, and priority operations
- administrator user, role, blocked-account, and reassignment operations

The frontend improves usability, but the FastAPI backend remains responsible
for authentication and authorization.
