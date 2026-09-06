# VOLTEX Backend + Database — Final Implementation Report

**Scope:** full backend + PostgreSQL schema for the existing VOLTEX Expo/RN app.
**Constraint honored:** no installs, no downloads, no external services, no database creation, no server start. All deliverables are source files, tests, config templates, migrations, and documentation only.

## 1. What Was Created

New top-level `backend/` folder (self-contained package):

```
backend/
├── pyproject.toml           # FastAPI, SQLAlchemy 2, Alembic, Pydantic v2, pytest
├── alembic.ini  + migrations/   (env.py, script.py.mako, 0001_initial.py)
├── .env.example
├── README.md
├── app/
│   ├── main.py              # FastAPI app, 69 routes, error envelope, health
│   ├── core/                # config, enums, exceptions, security, logging
│   ├── db/                  # Base(+naming/mixins), engine/session
│   ├── models/              # 15 SQLAlchemy models across all domains
│   ├── schemas/             # Pydantic v2 DTOs per domain
│   ├── services/            # business logic + transaction boundaries (15 modules)
│   ├── repositories/        # thin queries (users, sales)
│   ├── dependencies/        # JWT auth, RBAC, branch scope, pagination
│   ├── api/routes/          # 16 routers
│   └── utils/               # pagination, storage abstraction
├── scripts/seed.py          # deterministic fixtures, fixed UUIDs
└── tests/                   # 6 files: unit, integration, smoke, transactions
```

## 2. Database

24 PostgreSQL tables, one Alembic migration (`0001_initial.py`), server UUIDs via
`pgcrypto`, `citext` emails, UTC timestamps, named constraints, FK-safe ordering,
partial unique index (one open attendance shift per user), CHECK constraints for
quantity/price/length rules, and no photo binary in Postgres.

Groups: identity (`users`, `refresh_tokens`, `idempotency_keys`), organization
(`branches`), catalog (`products`), inventory (`branch_stock`,
`inventory_movements`, `stock_count_observations`), requests (`stock_requests`),
reviews, sales, attendance (`attendance_shifts`), photos (`shelf_photos`,
`photo_notes`), rewards (`reward_rules`, `point_ledger`, `lessons`,
`lesson_completions`, `challenges`, `challenge_enrollments`), notifications,
tasks, targets (`branch_targets`), audit (`audit_events`).

## 3. API (`/api/v1`)

`/login`, `/refresh`, `/logout`, `/me`, `/change-password`; users CRUD +
deactivate/reactivate; branches CRUD + active toggle; products CRUD + deactivate;
inventory stock/movements/counts/restock/adjust/transfer; sales list/create/cancel;
stock requests create/review/cancel/fulfill; reviews (polymorphic); attendance
clock-in/clock-out + shift list; photos upload + list + notes; rewards
(rules/ledger/lessons/challenges/leaderboard/summary); notifications; tasks;
targets + progress; audit; `sync/snapshot`. Standard error envelope, idempotency
keys (`Idempotency-Key` header), pagination params.

## 4. Authentication

bcrypt password hashing (12 rounds default, configurable); stateless 15-min JWT
access tokens (iss/aud/sub/role/branch_id/jti, HS256); opaque refresh tokens
stored as SHA-256 hashes with rotation (old revoked, replaced_by chained),
14-day expiry; logout revokes; change-password; last-login tracking.

## 5. RBAC + Authorization

Role→permission matrix in `dependencies/rbac.py`; FastAPI deps enforce role and
permission; branch-scoping (non-admins restricted to their branch); promoter
self-scope on sales/tasks/notifications; admin platform-wide. Permission set
explicitly excludes admin-only capabilities from promoter/supervisor roles.

## 6. Business Rules (enforced server-side)

Email unique (citext); promoter needs active, same-branch supervisor; last-active-
admin deactivation protection; supervisor with active promoters not deactivatable;
SKU unique/format; price non-negative, quantity bounds (sale 1–999, request
1–9999, count ≤99999); server-computed sale totals; count requires note when
observed≠reference and **never overwrites reference stock**; request state machine
with no-self-approval and dedicated transition endpoints; points via append-only
`point_ledger` (10/unit, 20/lesson) with reversal on sale cancellation; approved
request fulfillment adds stock + movement with continuity check
(`after = before + delta`).

## 7. Tests

Author and verify (run read-only, no database):

| Suite | Status |
|---|---|
| Auth primitives (hash/token round-trip) | 5 passed |
| RBAC matrix + branch scope | 5 passed |
| API smoke (health, validation envelope, auth guard, openapi) | 5 passed |
| Auth service integration | skip w/o DB (5 authored) |
| Business rules integration | skip w/o DB (10 authored) |
| Transactions integration | skip w/o DB (3 authored) |

Verification also covered: `compileall` clean, SQLAlchemy mapper configuration
clean, FastAPI app builds (69 routes). Deferred to a machine with PostgreSQL
installed: `alembic upgrade head` then `pytest -m integration`.

## 8. Documentation

`docs/backend-architecture.md`, `docs/database-schema.md`, `docs/domain-model.md`,
`docs/api-contract.md`, `docs/authentication.md`, `docs/authorization.md`,
`docs/offline-sync.md`, `docs/ci-cd.md`, plus `backend/README.md`.

## 9. Not Implemented (by design / out of scope)

- Running the server or executing migrations (prohibited).
- Client-side offline merge engine (spec in `docs/offline-sync.md`).
- Real S3 storage (abstraction + local-disk default implemented; boto3 optional).
- Push notifications, SMS, email sending, rate limiting providers.
- CI/CD pipeline execution (plan in `docs/ci-cd.md`).
- `alembic check` / mypy / ruff clean runs (prohibits fresh installs).
- Frontend wire-up (no API client, no auth storage swap).

## 10. Frontend Impact

**Existing frontend behavior was preserved.** No frontend file was modified; all
backend work lives under `backend/`. The next integration step is an API client
(tokens in AsyncStorage replacing/augmenting the demo provider) against the
documented contract.