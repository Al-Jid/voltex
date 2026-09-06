# VOLTEX CI/CD Plan

> **Status:** plan only. No CI/CD pipelines are configured or run in this phase.

## 1. Pipeline Stages

```
1. Lint (ruff format, ruff check)
      ↓
2. Type checking (mypy --strict)
      ↓
3. Unit tests (pytest -m unit)
      ↓
4. Integration tests (pytest -m integration, requires test PostgreSQL)
      ↓
5. Migration validation (alembic check)
      ↓
6. Security checks (pip-audit, bandit)
      ↓
7. Build Docker image (CI only)
      ↓
8. Deploy to environment (manual approval gates)
```

## 2. Environments

| Environment | Trigger | Purpose |
|---|---|---|
| development | push to `main` (CI smoke job only) | local dev, ephemeral DB |
| staging | tag `v*.*.*-rc.*` | staging-like deploy, real Postgres, manual load tests |
| production | tag `v*.*.*` | production |

## 3. Required Secrets

* `DATABASE_URL` (per env)
* `JWT_SECRET` (per env)
* `STORAGE_BACKEND` credentials
* `SENTRY_DSN` (future)

## 4. Database Migrations in CI

* `alembic upgrade head` runs against an ephemeral DB created from the latest migration on every PR.
* Migrations are **forward-only** in production (no auto-downgrade).

## 5. Test Stages

* Unit tests: pure Python, no DB, run on every PR.
* Integration tests: PostgreSQL via testcontainers OR docker-compose service. Required for any change that touches models, services, or routes.
* Coverage target: 85%+ on `app/services/`.

## 6. Release Checklist

1. Migrations tested against a copy of the staging DB.
2. CHANGELOG updated.
3. Tag created and signed.
4. Container image pushed to internal registry.
5. Deploy job runs `alembic upgrade head` then rolls the new image.
6. Smoke tests executed against `/health` and `/api/v1/auth/login` with seeded credentials.
7. Audit log and metrics reviewed.

## 7. Manual Gates

Production deploys require manual approval from a release manager.