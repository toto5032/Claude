# Claude CRUD App

A CRUD web application built with **FastAPI**, **SQLAlchemy**, and **SQLite**.

## Features

- RESTful API for item management (Create, Read, Update, Delete)
- Automatic API documentation (Swagger UI & ReDoc)
- Database migrations with Alembic
- Comprehensive test suite

## Requirements

- Python 3.11+

## Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -e ".[dev]"
```

## Running

```bash
uvicorn app.main:app --reload
```

The API will be available at:
- API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

| Method   | Endpoint          | Description       |
|----------|-------------------|-------------------|
| `GET`    | `/health`         | Health check      |
| `GET`    | `/items/`         | List all items    |
| `GET`    | `/items/{id}`     | Get item by ID    |
| `POST`   | `/items/`         | Create new item   |
| `PATCH`  | `/items/{id}`     | Update item       |
| `DELETE` | `/items/{id}`     | Delete item       |

## Testing

```bash
pytest
```

## Linting & Formatting

```bash
ruff check .          # Lint
ruff check . --fix    # Lint with auto-fix
black .               # Format
mypy app              # Type check
```

## Project Structure

```
├── app/
│   ├── main.py          # FastAPI application entry point
│   ├── config.py         # Application settings
│   ├── database.py       # Database engine and session
│   ├── models/           # SQLAlchemy ORM models
│   ├── schemas/          # Pydantic request/response schemas
│   └── routers/          # API route handlers
├── tests/                # Test suite
├── alembic/              # Database migrations
├── pyproject.toml        # Project configuration
└── CLAUDE.md             # AI assistant guidance
```
