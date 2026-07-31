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
