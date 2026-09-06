# VOLTEX Offline-First Synchronization Plan

> **Status:** architecture documented. The offline engine itself is **not implemented** in this phase.

## 1. Goals

When the Expo mobile app needs to operate offline (branch visit, weak network), the backend must:

1. Assign **stable, opaque, client-generated** identifiers for offline-created records.
2. Accept **idempotent submissions** so retries never create duplicates.
3. Provide **server-authoritative timestamps** so the client can resolve ordering.
4. Allow the client to **pull a snapshot** of the user's slice and replay missed updates.

## 2. Identifier Strategy

* `id` columns are UUIDs.
* When the client creates a record offline, it generates a UUID v4 locally and uses it in the `Idempotency-Key` header.
* On acceptance, the server returns the canonical record (with server `created_at`, `updated_at`, server `id` if different).
* If the client later submits the same UUID as the canonical `id`, the server accepts it as idempotent (no second insert).

## 3. Idempotency Table

`idempotency_keys`:

| Column | Type |
|---|---|
| key | text PK |
| user_id | uuid FK |
| endpoint | text |
| request_fingerprint | sha256(method+path+body) |
| response_status | int |
| response_body | jsonb |
| created_at | timestamptz |
| expires_at | timestamptz (24h) |

Behavior:

1. Client sends `Idempotency-Key: <uuid>` on a mutation.
2. Server computes fingerprint. If key exists:
   * Same fingerprint → return cached response.
   * Different fingerprint → `409 IDEMPOTENCY_KEY_MISMATCH`.
3. Server processes the request, stores response, returns.

## 4. Sync Snapshot

`GET /api/v1/sync/snapshot` returns the latest `updated_at` per entity for the caller's scope:

```json
{
  "scope": "promoter",
  "branch_id": "...",
  "servers": {
    "products": "2026-09-06T12:34:56Z",
    "branch_stock": "2026-09-06T12:34:56Z",
    "sales": "2026-09-06T12:34:56Z",
    "stock_requests": "2026-09-06T12:34:56Z",
    "shelf_photos": "2026-09-06T12:34:56Z",
    "lessons": "2026-09-06T12:34:56Z",
    "notifications": "2026-09-06T12:34:56Z"
  }
}
```

Follow-up calls (e.g. `GET /api/v1/sales?since=2026-09-06T12:34:56Z`) return only records with `updated_at > since`. The client merges by `id`.

## 5. Conflict Resolution

| Entity | Strategy |
|---|---|
| Sales | server-authoritative; offline draft, server is final. If client posts the same payload twice, the second is a no-op due to idempotency. |
| Stock requests | client may draft locally; submission is idempotent. Server decides status; client cannot mutate status. |
| Stock counts | append-only ledger; conflicts impossible by design. |
| Photo notes | last-write-wins by `updated_at`. Editing invalidates existing review. |
| Notifications | server-only; client may not create. |
| Tasks | server-authoritative transitions (`complete`, `reopen`). |

## 6. What This Phase Delivers

* Idempotency table + service (`app/services/idempotency.py`).
* Idempotency-Key required on documented mutating endpoints.
* `updated_at` columns everywhere with auto-update trigger or SQLAlchemy `onupdate=func.now()`.
* `GET /api/v1/sync/snapshot` endpoint (returns minimal cursor metadata).
* `since` filter on list endpoints where the client uses it.

## 7. What Is Postponed

* Full conflict-aware offline merge engine on the client.
* Background sync worker / OS scheduling.
* Queue priority / bandwidth policies.
* Multi-device session handling.
* Push-queue reconciliation.