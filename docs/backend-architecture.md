# VOLTEX Backend Architecture Assessment

## 1. Context

The VOLTEX mobile application is an advanced interactive prototype built with Expo SDK 57 + React Native 0.86.3 + React 19.2.3 + TypeScript. It contains 48 fully implemented screens across three roles:

* **Promoter** — 25 screens
* **Supervisor** — 9 screens
* **Admin** — 13 screens
* **RolePicker** — 1 screen

Current data layer:

* `PreferencesProvider` — language + theme (light/dark/system)
* `DemoProvider` — promoter records (sales, requests, shifts, photos, counts, profile, drafts, lessons, notifications)
* `ManagementProvider` — staff, branches, catalog, reviews, tasks, targets, audit
* `AsyncStorage` — three versioned keys: `@voltex/preferences/v1`, `@voltex/demo/v1`, `@voltex/management/v1`

All persistence is local. All business validation lives in the frontend. There is no backend, no authentication, no RBAC enforcement, and no server-side data.

## 2. Goals of the Backend Phase

1. Build a complete production-ready backend that preserves the existing business behavior.
2. Enforce all business rules server-side.
3. Provide stable contracts for a future frontend migration from `AsyncStorage` to HTTP.
4. Lay the foundation for real authentication, RBAC, transactional business logic, and an eventual offline-sync layer.

## 3. Backend Technology Decision

### Options considered

| Option | Pros | Cons |
|---|---|---|
| Supabase | Fast to bootstrap, Postgres + Auth + Storage + RLS out of the box | Opinionated, harder to encode complex business rules (e.g. last-active-admin, supervisor reassignment), RLS becomes the security boundary which is harder to test, BaaS coupling |
| **FastAPI + PostgreSQL + SQLAlchemy 2.x + Alembic + Pydantic v2** | Full control, explicit RBAC dependencies, easy unit testing, type-safe schemas, transactional control, modular monolith | More code to write |

### Decision

**FastAPI + PostgreSQL + SQLAlchemy 2.x + Alembic + Pydantic v2** as a **modular monolith**.

Justification:

* The VOLTEX domain has rich business invariants (last-active-admin, supervisor reassignment, branch-active guard, sales affecting inventory transactionally, etc.) that benefit from explicit service code.
* RBAC for promoter/supervisor/admin is not a single `role == 'admin'` check; we need reusable FastAPI dependencies.
* The future offline-sync engine requires server-defined contracts (cursor, idempotency keys, server timestamps) that fit a custom REST/JSON contract better than a generated one.
* The product roadmap explicitly calls for Supabase as a *future* deployment target; keeping the FastAPI backend portable to Supabase Postgres (or to any managed Postgres) is straightforward.

### Rejected infrastructure

* No Redis, Kafka, RabbitMQ, Celery, Elasticsearch, microservices — none are required by the current requirements.

## 4. Target Architecture

```
backend/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── exceptions.py
│   │   ├── logging.py
│   │   └── enums.py
│   ├── db/
│   │   ├── base.py
│   │   ├── session.py
│   │   └── dependencies.py
│   ├── models/                 # SQLAlchemy ORM
│   │   ├── mixins.py
│   │   ├── identity.py
│   │   ├── organization.py
│   │   ├── catalog.py
│   │   ├── inventory.py
│   │   ├── sales.py
│   │   ├── requests.py
│   │   ├── reviews.py
│   │   ├── attendance.py
│   │   ├── photos.py
│   │   ├── rewards.py
│   │   ├── notifications.py
│   │   ├── tasks.py
│   │   ├── targets.py
│   │   └── audit.py
│   ├── schemas/                # Pydantic v2
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── branch.py
│   │   ├── product.py
│   │   ├── inventory.py
│   │   ├── sale.py
│   │   ├── request.py
│   │   ├── review.py
│   │   ├── attendance.py
│   │   ├── photo.py
│   │   ├── reward.py
│   │   ├── notification.py
│   │   ├── task.py
│   │   ├── target.py
│   │   ├── audit.py
│   │   └── common.py
│   ├── api/
│   │   ├── router.py
│   │   └── routes/
│   │       ├── health.py
│   │       ├── auth.py
│   │       ├── users.py
│   │       ├── branches.py
│   │       ├── products.py
│   │       ├── inventory.py
│   │       ├── sales.py
│   │       ├── requests.py
│   │       ├── reviews.py
│   │       ├── attendance.py
│   │       ├── photos.py
│   │       ├── rewards.py
│   │       ├── notifications.py
│   │       ├── tasks.py
│   │       ├── targets.py
│   │       └── audit.py
│   ├── services/               # business logic
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── branch_service.py
│   │   ├── product_service.py
│   │   ├── inventory_service.py
│   │   ├── sales_service.py
│   │   ├── request_service.py
│   │   ├── review_service.py
│   │   ├── attendance_service.py
│   │   ├── photo_service.py
│   │   ├── reward_service.py
│   │   ├── notification_service.py
│   │   ├── task_service.py
│   │   ├── target_service.py
│   │   └── audit_service.py
│   ├── repositories/           # thin SQL persistence layer
│   │   ├── base.py
│   │   └── ... (one per aggregate if helpful)
│   ├── dependencies/           # FastAPI deps: auth, pagination, RBAC
│   │   ├── auth.py
│   │   ├── pagination.py
│   │   └── permissions.py
│   ├── utils/                  # idempotency, storage abstraction, time, slug
│   │   ├── storage.py
│   │   ├── pagination.py
│   │   ├── time.py
│   │   └── currency.py
│   └── errors.py
├── migrations/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── tests/
│   ├── conftest.py
│   ├── auth/
│   ├── users/
│   ├── branches/
│   ├── products/
│   ├── inventory/
│   ├── sales/
│   ├── requests/
│   ├── reviews/
│   ├── attendance/
│   ├── photos/
│   ├── rewards/
│   ├── notifications/
│   ├── tasks/
│   ├── targets/
│   └── audit/
├── pyproject.toml
├── alembic.ini
├── .env.example
├── docker-compose.yml          # optional, not auto-run
└── README.md
```

Layer responsibilities:

| Layer | Responsibility |
|---|---|
| `api/routes/*` | HTTP shape only: parse, validate, call service, return response. No business rules. |
| `services/*` | Pure business logic. Transaction boundaries enforced here. Calls repositories and other services. |
| `repositories/*` | Thin ORM queries. No business decisions. |
| `models/*` | SQLAlchemy tables, relationships, constraints. |
| `schemas/*` | Pydantic request/response DTOs. No DB access. |
| `dependencies/*` | FastAPI reusable injection: `get_current_user`, `require_role`, pagination. |
| `core/*` | Cross-cutting: config, security, exceptions, logging. |

## 5. Key Architectural Choices

* **UUID primary keys** everywhere (`uuid` column). Stable identifiers across sync.
* **Server-controlled timestamps** (`created_at`, `updated_at`). UTC.
* **Soft deactivation** for users, branches, products (`is_active`).
* **Hard preservation** for sales, attendance, reviews, rewards ledger.
* **State machines** for `Sale`, `Request`, `Review`, `AttendanceShift`, `Task`. Transitions enforced server-side, not by free-form field mutation.
* **Ledger-based rewards** instead of a mutable `user.points` field.
* **Inventory** modeled as `branch_stock` snapshots + `inventory_movements` ledger. Counts and sales are movements, not direct overwrites.
* **Photo metadata** is in Postgres; binary blobs go through a `StorageBackend` abstraction (local disk impl for dev; S3-compatible later).
* **Idempotency** for `POST /sales`, `POST /attendance/check-in`, `POST /inventory/counts`, `POST /requests`, `POST /reviews`, `POST /tasks` via `Idempotency-Key` header + `idempotency_keys` table.
* **JWT** access tokens + refresh tokens stored server-side as hashed records (rotation + revocation).
* **RBAC** as FastAPI dependencies (`require_promoter`, `require_supervisor`, `require_admin`) + resource-scope checks (`assert_can_access_user`, `assert_can_review`).
* **No business logic** inside route handlers — only HTTP plumbing.

## 6. Explicit Non-Goals (Phase 1)

* No real object storage (S3/MinIO) — local disk implementation behind `StorageBackend`.
* No push notifications (FCM/APNs/Expo Push).
* No biometric auth.
* No offline-sync engine (only `sync/snapshot` placeholder).
* No full-text search engine.
* No background workers.
* No multi-tenant organization partitioning (one VOLTEX organization assumed; migrations in place to add `organization_id` later).

## 7. Acceptance Criteria Mapping

| Section | Where it lives |
|---|---|
| Clean modular structure | This folder layout |
| DB schema | `docs/database-schema.md` + Alembic migration |
| Authentication | `app/services/auth_service.py` + `app/dependencies/auth.py` |
| Authorization | `app/dependencies/permissions.py` + per-resource checks |
| API versioning | `/api/v1` prefix on all routers |
| Error format | `app/core/exceptions.py` + `app/main.py` exception handlers |
| Pagination | `app/utils/pagination.py` + `app/dependencies/pagination.py` |
| Transactions | `app/services/*` + `app/db/session.py` `get_db()` |
| Idempotency | `app/services/idempotency.py` + `idempotency_keys` table |
| Configuration | `app/core/config.py` + `.env.example` |
| Tests | `tests/` |
| Documentation | `docs/` |
| CI/CD plan | `docs/ci-cd.md` |