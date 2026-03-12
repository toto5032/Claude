# CLAUDE.md

This file provides guidance for AI assistants (like Claude) working in this repository.

## Repository Overview

- **Repository**: toto5032/Claude
- **Tech Stack**: Python 3.11+ / FastAPI / SQLAlchemy 2.0 / PostgreSQL
- **Type**: CRUD web application with RESTful API

## Getting Started

```bash
# With Docker (recommended)
docker compose up --build

# Local development
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
docker compose up db -d    # start PostgreSQL
alembic upgrade head       # run migrations
```

## Common Commands

```bash
# Run the dev server (local)
uvicorn app.main:app --reload

# Docker
docker compose up --build     # start all services
docker compose up db -d       # start only PostgreSQL

# Run tests
pytest
pytest -v                 # verbose output

# Linting & formatting
ruff check .              # lint
ruff check . --fix        # lint with auto-fix
black .                   # format code
black --check .           # check formatting without changes
mypy app                  # type checking
```

## Project Structure

```
├── app/
│   ├── main.py           # FastAPI app entry point, includes router
│   ├── config.py          # Settings via pydantic-settings (env: APP_*)
│   ├── database.py        # SQLAlchemy engine, session, Base class
│   ├── models/            # SQLAlchemy ORM models
│   │   └── item.py        # Item model
│   ├── schemas/           # Pydantic request/response schemas
│   │   └── item.py        # ItemCreate, ItemUpdate, ItemResponse
│   └── routers/           # API route handlers
│       └── items.py       # CRUD endpoints for /items
├── tests/
│   ├── conftest.py        # Test fixtures (client, db session)
│   └── test_items.py      # Item endpoint tests
├── alembic/               # Database migrations
├── .github/workflows/
│   └── ci.yml             # CI pipeline (lint, format, type check, test)
├── pyproject.toml         # Project config (deps, ruff, black, mypy, pytest)
├── Dockerfile             # Container image definition
├── docker-compose.yml     # Docker Compose services (app + PostgreSQL)
├── .dockerignore          # Docker build exclusions
├── .gitignore
├── README.md
└── CLAUDE.md              # This file
```

## Architecture & Patterns

- **Layered structure**: routers → models/schemas → database
- **Dependency injection**: FastAPI `Depends(get_db)` for database sessions
- **Pydantic v2**: Schemas use `model_config = {"from_attributes": True}` for ORM compatibility
- **SQLAlchemy 2.0 style**: `Mapped[]` type annotations for model columns
- **Settings**: `pydantic-settings` with `APP_` env prefix (e.g., `APP_DATABASE_URL`)

## Development Workflow

### Branching

- Feature branches: `claude/<description>-<id>`
- Never push directly to `main`.

### Commits

- Clear, descriptive commit messages.
- One logical change per commit.
- Never commit secrets, `.env` files, or `*.db` files.

### Adding New Resources

To add a new CRUD resource (e.g., "User"):

1. Create model in `app/models/user.py` — add to `app/models/__init__.py`
2. Create schemas in `app/schemas/user.py` — add to `app/schemas/__init__.py`
3. Create router in `app/routers/users.py`
4. Register router in `app/main.py` via `app.include_router()`
5. Add tests in `tests/test_users.py`

### Code Conventions

- Line length: 88 characters (Black default)
- Imports sorted by ruff (isort rules)
- Type hints required on all function signatures
- Use `str | None` union syntax (Python 3.11+)

## CI Pipeline

GitHub Actions runs on push/PR to `main` with PostgreSQL service container:
1. Ruff lint check
2. Black format check
3. Mypy type check
4. Pytest test suite

Matrix: Python 3.11 and 3.12.

## AI Assistant Guidelines

1. **Read before writing** — Understand existing code before making changes.
2. **Stay focused** — Only make changes that are directly requested.
3. **Don't over-engineer** — No unnecessary abstractions or premature generalization.
4. **Be security-conscious** — Never commit secrets; avoid OWASP top-10 vulnerabilities.
5. **Test your changes** — Run `pytest` and `ruff check .` before committing.
6. **Follow existing patterns** — Match the layered architecture when adding new features.
7. **Update docs** — Keep this file and README current as the project evolves.
