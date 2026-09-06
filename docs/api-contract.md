# VOLTEX API Contract

All endpoints are prefixed with `/api/v1` and respond with JSON. The contract is versioned; breaking changes will land under `/api/v2`.

## 1. Conventions

### Content Types

* `application/json; charset=utf-8` for all requests/responses.

### Authentication

* Required for all endpoints except `/api/v1/auth/login`, `/api/v1/auth/refresh`, `/api/v1/health`, `/api/v1/health/ready`.
* Header: `Authorization: Bearer <access_token>`.
* Access token TTL: 15 minutes (configurable). Refresh token TTL: 14 days.

### Idempotency

* Required header for mutating endpoints: `Idempotency-Key: <client-uuid>`.
* TTL: 24 hours.
* Fingerprinted on method + path + body. Same key with different fingerprint → `409 IDEMPOTENCY_KEY_MISMATCH`.

### Pagination

* Query parameters: `page` (1-indexed, default 1), `page_size` (default 20, max 100).
* Response envelope:
  ```json
  {
    "items": [...],
    "page": 1,
    "page_size": 20,
    "total": 137
  }
  ```

### Filtering / Sorting

* Search: `q=<text>` for name/email/SKU.
* Specific filters per resource (e.g. `?role=promoter&is_active=true`).
* Sort: `sort=created_at:desc,name:asc`. Default `created_at:desc`.

### Errors

Standard error envelope (see `app/core/exceptions.py`):

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Product not found",
    "details": { "id": "..." }
  }
}
```

Codes used:

| HTTP | code | when |
|---|---|---|
| 400 | `BAD_REQUEST` | malformed body |
| 401 | `UNAUTHENTICATED` | missing/expired token |
| 403 | `FORBIDDEN` | role/scope violation |
| 404 | `RESOURCE_NOT_FOUND` | entity missing or out of scope |
| 409 | `CONFLICT` | unique constraint, business invariant |
| 409 | `IDEMPOTENCY_KEY_MISMATCH` | same key, different body |
| 422 | `VALIDATION_ERROR` | Pydantic validation |
| 429 | `RATE_LIMITED` | (future) |
| 500 | `INTERNAL_ERROR` | unexpected |

## 2. Auth Endpoints

### `POST /api/v1/auth/login`

```json
{ "email": "hassan@example.test", "password": "..." }
```

Response `200`:

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "Bearer",
  "expires_in": 900,
  "user": {
    "id": "...",
    "email": "...",
    "display_name": "Hassan Gamal",
    "role": "promoter",
    "branch_id": "...",
    "supervisor_id": "..."
  }
}
```

Errors: 401 (`INVALID_CREDENTIALS`), 403 (`USER_INACTIVE`).

### `POST /api/v1/auth/refresh`

```json
{ "refresh_token": "..." }
```

Response `200`: same shape as login (rotates refresh token).

Errors: 401 (`REFRESH_INVALID`, `REFRESH_EXPIRED`).

### `POST /api/v1/auth/logout`

Body: `{ "refresh_token": "..." }` — revokes the refresh token. Idempotent.

### `GET /api/v1/auth/me`

Returns the current authenticated user.

## 3. Users

### `GET /api/v1/users`

Admin only. Supports `q`, `role`, `is_active`, `branch_id`, `supervisor_id`, pagination, sort.

### `POST /api/v1/users`

Admin only.

```json
{
  "email": "...",
  "display_name": "...",
  "phone": "...",
  "password": "...",
  "role": "promoter",
  "branch_id": "...",
  "supervisor_id": "...",   // required when role=promoter
  "is_active": true
}
```

Errors: 409 (`EMAIL_ALREADY_EXISTS`), 422, 403.

### `GET /api/v1/users/{id}`

Admin: any user.
Supervisor: only assigned team members.
Promoter: only self.

### `PATCH /api/v1/users/{id}`

Admin only. Cannot change own role to non-admin if it would leave zero active admins.

### `POST /api/v1/users/{id}/activate`, `POST /api/v1/users/{id}/deactivate`

Convenience actions with the relevant business rules.

### `POST /api/v1/users/{id}/reset-password` (admin)

```json
{ "new_password": "..." }
```

## 4. Branches

### `GET /api/v1/branches`

Admin/supervisor: all branches. Promoter: only own branch.

### `POST /api/v1/branches` (admin)

### `PATCH /api/v1/branches/{id}` (admin)

Cannot deactivate if active staff assigned.

### `GET /api/v1/branches/{id}/staff`

Admin/supervisor.

## 5. Products (Catalog)

### `GET /api/v1/products`

Public to authenticated users. `q`, `is_active`, pagination.

### `POST /api/v1/products` (admin)

```json
{
  "sku": "VX-AC12",
  "name": "VOLTEX Air 12",
  "name_ar": "فولتكس إير 12",
  "price": 18500.00,
  "daily_target": 8
}
```

### `PATCH /api/v1/products/{id}` (admin)

### `POST /api/v1/products/{id}/archive`, `POST /api/v1/products/{id}/restore` (admin)

## 6. Inventory

### `GET /api/v1/inventory`

Returns `branch_stock` rows for the caller's branch (promoter) or query param `branch_id` (admin/supervisor).

### `POST /api/v1/inventory/counts`

Promoter submits an observation. Idempotent.

```json
{
  "branch_id": "...",
  "product_id": "...",
  "observed_quantity": 4,
  "note": "Shelf missing 2 units from previous day"
}
```

`note` REQUIRED when `observed_quantity != reference_quantity`.

Errors: 409 (`COUNT_REQUIRES_NOTE`), 422.

### `GET /api/v1/inventory/counts`

Filter by branch/product/observer/date range.

### `GET /api/v1/inventory/movements`

Filter by branch/product/type/date range. Admin/supervisor.

## 7. Sales

### `GET /api/v1/sales`

Promoter: only own sales. Supervisor: assigned team. Admin: all.
Filters: `date_from`, `date_to`, `promoter_id`, `branch_id`, `product_id`, `period=today|week|month`.

### `POST /api/v1/sales` (promoter)

Idempotent.

```json
{
  "product_id": "...",
  "quantity": 1,
  "note": "..."
}
```

Server computes `unit_price` (from current `products.price`) and `total_amount`. Body cannot override.

Errors: 422 (`INVALID_QUANTITY`), 404 (`PRODUCT_NOT_FOUND`), 409 (`PRODUCT_INACTIVE`).

### `GET /api/v1/sales/{id}`

Scope check.

## 8. Requests

### `GET /api/v1/requests`

Promoter: own. Supervisor: assigned team. Admin: all.

Filters: `status`, `request_type`, `requester_id`, `date_from`, `date_to`.

### `POST /api/v1/requests` (promoter)

Idempotent.

```json
{
  "request_type": "restock",
  "product_id": "...",
  "quantity": 6,
  "reason": "Branch needs more for weekend",
  "destination_branch_id": "..."
}
```

### `GET /api/v1/requests/{id}`

### `POST /api/v1/requests/{id}/approve` (supervisor)

Cannot approve own request (no self-approval).

### `POST /api/v1/requests/{id}/request-changes` (supervisor)

```json
{ "decision_note": "..." }   // ≥ 5 chars
```

Sets `status = changes_requested` and creates a `reviews` row.

### `POST /api/v1/requests/{id}/cancel` (requester)

Only when status is `pending`.

### `POST /api/v1/requests/{id}/fulfill` (admin/supervisor)

Only allowed when status is `approved`. Emits an inventory movement.

## 9. Reviews

### `GET /api/v1/reviews`

Supervisor: own reviews + reviews of team. Admin: all.

### `POST /api/v1/reviews` (supervisor)

```json
{
  "target_type": "stock_request",
  "target_id": "...",
  "decision": "changes_requested",
  "note": "..."
}
```

Errors: 409 (`NOT_IN_SCOPE`) if requester/photo not in supervisor's team, 409 (`REQUEST_ALREADY_DECIDED`).

## 10. Attendance

### `GET /api/v1/attendance`

Filter: `user_id`, `branch_id`, `date_from`, `date_to`.

Promoter: own only.

### `POST /api/v1/attendance/check-in`

Idempotent. Returns existing open shift if one is already active.

Errors: 409 (`USER_INACTIVE`), 403.

### `POST /api/v1/attendance/check-out`

Idempotent. Closes current open shift.

### `GET /api/v1/attendance/active`

Returns the open shift for the caller (or 404).

## 11. Photos

### `POST /api/v1/photos`

`multipart/form-data`:

* `file` (binary)
* `source` (`camera`|`library`)
* `note` (optional)
* `latitude` (optional)
* `longitude` (optional)

Idempotent.

### `GET /api/v1/photos`

Filters: `uploader_id`, `branch_id`, `date_from`, `date_to`.

### `GET /api/v1/photos/{id}`

Returns metadata + presigned URL (or local download URL in dev).

### `PATCH /api/v1/photos/{id}` (uploader)

Update note. Editing notes deactivates the existing review.

### `DELETE /api/v1/photos/{id}` (uploader or admin)

Removes the file from storage and marks the row inactive.

## 12. Rewards

### `GET /api/v1/rewards/me`

Returns current balance and per-rule totals for the caller.

```json
{
  "balance": 240,
  "by_rule": [
    { "rule_code": "sale_unit", "points": 200 },
    { "rule_code": "lesson_complete", "points": 40 }
  ]
}
```

### `GET /api/v1/rewards/ledger`

Paginated ledger entries for caller (or any user if admin/supervisor with scope).

### `GET /api/v1/leaderboard`

Query: `scope=branch|team`, optional `branch_id`, `period=today|week|month`.

### `POST /api/v1/rewards/rules` (admin)

### `GET /api/v1/rewards/rules`

### `POST /api/v1/lessons/{id}/complete`

Idempotent.

### `POST /api/v1/challenges/{code}/join`

Idempotent.

### `GET /api/v1/challenges`, `GET /api/v1/challenges/{code}`

### `GET /api/v1/challenges/{code}/enrollment` (caller's enrollment)

## 13. Tasks

### `GET /api/v1/tasks`

Assignee: own. Assigner: own created. Admin: all.

### `POST /api/v1/tasks` (supervisor)

```json
{
  "assignee_id": "...",
  "title": "Re-train team on photo guidelines",
  "due_date": "2026-09-15"
}
```

Errors: 409 (`ASSIGNEE_NOT_IN_TEAM`).

### `PATCH /api/v1/tasks/{id}` (assigner)

Update title/due_date.

### `POST /api/v1/tasks/{id}/complete` (assignee or assigner)

### `POST /api/v1/tasks/{id}/reopen` (assigner or admin)

## 14. Targets

### `GET /api/v1/targets`

Filters: `branch_id`, `period_type`, `is_active`.

### `POST /api/v1/targets` (admin)

### `PATCH /api/v1/targets/{id}` (admin)

### `GET /api/v1/targets/active?branch_id=...`

Returns the currently active target for the branch (used by Promoter Home).

## 15. Notifications

### `GET /api/v1/notifications`

Filters: `is_read`, `type`.

### `PATCH /api/v1/notifications/{id}/read`

### `POST /api/v1/notifications/mark-all-read`

## 16. Audit

### `GET /api/v1/audit` (admin)

Filters: `actor_id`, `actor_role`, `action`, `entity_type`, `entity_id`, `date_from`, `date_to`, pagination.

## 17. Sync (placeholder)

### `GET /api/v1/sync/snapshot`

Returns the latest server `updated_at` for each entity so a future client can perform incremental sync. The shape:

```json
{
  "servers": {
    "users": "2026-09-06T12:34:56Z",
    "sales": "2026-09-06T12:34:56Z",
    "stock_requests": "2026-09-06T12:34:56Z"
  }
}
```

This endpoint is provided but **the offline engine itself is not implemented** in this phase.

## 18. Rate Limits (future)

Out of scope for v1. Recommended plan: 60 req/min for mutations per user.

## 19. Versioning Policy

* `/api/v1/...` is the current contract.
* Deprecations announced via `Sunset` header.
* New major versions land under `/api/v2`.