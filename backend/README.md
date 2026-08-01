# Helpdesk Platform Backend

Backend API for the Helpdesk Platform, built with FastAPI.

## Requirements

- Python 3.13 or newer
- [uv](https://docs.astral.sh/uv/)

## Installation

From the `backend` directory, install the project dependencies:

```bash
uv sync
```

## Running the application

Start the development server:

```bash
uv run uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## Running tests

Run the test suite:

```bash
uv run pytest
```

Run tests that do not require external services:

```bash
uv run pytest -m "not integration"
```

Database integration tests require the local PostgreSQL service:

```bash
docker compose up -d db
```

Run only database integration tests:

```bash
uv run pytest -m integration
```

## Code quality

Check formatting without changing files:

```bash
uv run ruff format --check .
```

Run the linter:

```bash
uv run ruff check .
```

Run static type checking:

```bash
uv run mypy app tests
```

## API documentation

When the application is running, Swagger UI is available at
`http://127.0.0.1:8000/docs`.

The health-check endpoint is available at
`http://127.0.0.1:8000/health`.

## Configuration

Application settings are managed with Pydantic Settings.

For local development, create a `.env` file from the provided example:

```bash
cp .env.example .env
```

Available environment variables:

| Variable | Default value | Description |
|---|---|---|
| `HELPDESK_APP_NAME` | `Helpdesk API` | Application name displayed in the API documentation |
| `HELPDESK_APP_VERSION` | `0.1.0` | Current API version |
| `HELPDESK_ENVIRONMENT` | `development` | Application environment: `development`, `testing`, or `production` |
| `HELPDESK_DEBUG` | `false` | Enables or disables FastAPI debug mode |
| `HELPDESK_API_V1_PREFIX` | `/api/v1` | Prefix for version 1 API routes |
| `HELPDESK_DATABASE_URL` | `postgresql+asyncpg://helpdesk:helpdesk_password@localhost:5433/helpdesk` | Asynchronous SQLAlchemy database connection URL |

The `.env` file is intended for local settings and must not be committed. The `.env.example` file contains safe example values and should remain in version control.

Run Docker Compose commands from the repository root.
