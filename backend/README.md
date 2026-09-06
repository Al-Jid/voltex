# VOLTEX Backend

FastAPI + PostgreSQL backend for the VOLTEX mobile application. Replaces the current local/demo data layer (AsyncStorage + Context API) with real authentication, RBAC, transactional business logic, and a stable contract for offline-first sync.

## Quick start (developer)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env

# Postgres must be running. See docs/database-schema.md for required extensions.
alembic upgrade head
python -m scripts.seed          # deterministic dev fixtures
uvicorn app.main:app --reload --port 8000
```

> This task created the code, migrations, configuration templates, tests, and documentation only. No packages were installed, no databases were created, no servers were started.

## Architecture

See `docs/backend-architecture.md`.

```
backend/
├── app/
│   ├── main.py                  # FastAPI entrypoint
│   ├── core/                    # config, security, exceptions, logging
│   ├── db/                      # SQLAlchemy session + base + deps
│   ├── models/                  # ORM tables
│   ├── schemas/                 # Pydantic v2 DTOs
│   ├── api/routes/              # HTTP layer only
│   ├── services/                # business logic + transactions
│   ├── repositories/            # thin ORM queries
│   ├── dependencies/            # FastAPI deps (auth, pagination, RBAC)
│   └── utils/                   # storage abstraction, pagination, etc.
├── migrations/                  # Alembic
├── scripts/                     # seed + utility scripts
├── tests/                       # pytest
├── pyproject.toml
├── alembic.ini
└── .env.example
```

## Documents

| Document | Topic |
|---|---|
| `docs/backend-architecture.md` | Overall architecture decisions |
| `docs/database-schema.md` | Full PostgreSQL schema |
| `docs/domain-model.md` | Frontend → backend mapping |
| `docs/api-contract.md` | REST endpoints, error format, pagination |
| `docs/authentication.md` | JWT + refresh tokens |
| `docs/authorization.md` | RBAC + business rules |
| `docs/offline-sync.md` | Future offline-first sync |
| `docs/ci-cd.md` | Pipeline plan |

## Tests

```bash
pytest -m unit              # fast, no DB
pytest -m integration       # requires PostgreSQL
pytest --cov=app            # coverage report
```

Without `DATABASE_URL`, integration tests are skipped automatically.

**Verification performed in this task (all read-only):**
- `python -m compileall` over `app`, `migrations`, `tests`, `scripts` — clean.
- SQLAlchemy mapper configuration — clean.
- FastAPI app builds with all 69 registered routes.
- `pytest tests/test_api_smoke.py` — 5 passed.
- `pytest tests/test_auth_unit.py tests/test_rbac_unit.py` — 13 passed.
- Integration tests (auth flow, business rules, transactions) are authored and skip cleanly without a database.

## API

`/api/v1/...` — see `docs/api-contract.md` for the full contract.

Health: `GET /health`, `GET /health/ready`.

## License

Proprietary.