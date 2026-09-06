# VOLTEX Domain Model

This document maps every existing frontend concept to a backend domain, database table, and API endpoint.

## 1. Identity Domain

### 1.1 User

| Concept | Source | Notes |
|---|---|---|
| Backend domain | `User` aggregate | Replaces the implicit `state.profile` of `DemoProvider` |
| Database table | `users` | Stable UUID PK |
| API | `POST /api/v1/auth/login`, `GET /api/v1/users`, `PATCH /api/v1/users/{id}`, `POST /api/v1/auth/logout`, `GET /api/v1/auth/me` |

Fields:

* `id` UUID PK
* `email` citext UNIQUE NOT NULL — replaces the username reference in login prototype
* `display_name` text NOT NULL — replaces `state.profile.name`
* `phone` text NULL — replaces `state.profile.phone`
* `password_hash` text NOT NULL
* `role` enum('promoter','supervisor','admin') NOT NULL — replaces `Staff.role`
* `branch_id` UUID NOT NULL FK → branches
* `supervisor_id` UUID NULL FK → users — replaces `Staff.supervisorId`
* `is_active` boolean NOT NULL DEFAULT TRUE — replaces `Staff.active`
* `must_change_password` boolean NOT NULL DEFAULT FALSE
* `last_login_at` timestamptz NULL
* `created_at`, `updated_at` timestamptz NOT NULL

Business rules preserved from frontend:

* Email must be unique.
* Promoters must have a non-empty supervisor.
* A supervisor must be `supervisor` role and active.
* A branch must exist and be active when assigning a non-inactive user.
* Cannot deactivate or change role away from `admin` if it would leave zero active admins.
* Cannot deactivate or change role away from `supervisor` if they still have active promoters assigned.

### 1.2 Session / RefreshToken

Replaces nothing (frontend does not have auth).

| Concept | Source |
|---|---|
| Table | `refresh_tokens` |
| API | `POST /api/v1/auth/refresh`, `POST /api/v1/auth/logout` |

Fields:

* `id` UUID PK
* `user_id` UUID FK → users
* `token_hash` text NOT NULL UNIQUE
* `issued_at` timestamptz NOT NULL
* `expires_at` timestamptz NOT NULL
* `revoked_at` timestamptz NULL
* `replaced_by_id` UUID NULL FK → refresh_tokens (rotation)
* `user_agent` text NULL
* `ip` text NULL

### 1.3 IdempotencyKey

| Concept | Source |
|---|---|
| Table | `idempotency_keys` |
| API | Required for mutation endpoints via `Idempotency-Key` header |

Fields:

* `key` text PK
* `user_id` UUID FK → users
* `endpoint` text NOT NULL
* `request_fingerprint` text NOT NULL
* `response_status` int NULL
* `response_body` jsonb NULL
* `created_at`, `expires_at` timestamptz NOT NULL

## 2. Organization Domain

### 2.1 Branch

Replaces `ManagementProvider.branches`.

| Concept | Source |
|---|---|
| Table | `branches` |
| API | `GET /api/v1/branches`, `POST /api/v1/branches`, `PATCH /api/v1/branches/{id}` |

Fields:

* `id` UUID PK
* `code` text UNIQUE NOT NULL — replaces implicit `id` `b1/b2/b3`
* `name` text NOT NULL UNIQUE
* `address` text NULL
* `is_active` boolean NOT NULL DEFAULT TRUE
* `created_at`, `updated_at`

Business rules:

* Name unique.
* Cannot deactivate a branch that has active staff assigned.

## 3. Catalog Domain

### 3.1 Product

Replaces `ManagementProvider.catalog` and `DemoProvider.products`.

| Concept | Source |
|---|---|
| Table | `products` |
| API | `GET /api/v1/products`, `POST /api/v1/products`, `PATCH /api/v1/products/{id}` |

Fields:

* `id` UUID PK
* `sku` text UNIQUE NOT NULL — replaces `product.sku`
* `name` text NOT NULL
* `name_ar` text NULL
* `description` text NULL
* `price` numeric(12,2) NOT NULL CHECK (price >= 0) — EGP
* `is_active` boolean NOT NULL DEFAULT TRUE
* `daily_target` int NULL — replaces `Product.target`
* `created_at`, `updated_at`

### 3.2 ProductLocalizedName (optional in v1)

Out of scope for v1. Locale-specific names handled via `name_ar` column above.

## 4. Inventory Domain

This domain is intentionally NOT a single `product.stock` column.

### 4.1 BranchStock (snapshot)

| Concept | Source |
|---|---|
| Table | `branch_stock` |
| API | `GET /api/v1/inventory` |

Fields:

* `id` UUID PK
* `branch_id` UUID FK → branches NOT NULL
* `product_id` UUID FK → products NOT NULL
* `quantity` integer NOT NULL DEFAULT 0 CHECK (quantity >= 0)
* `updated_at` timestamptz NOT NULL
* UNIQUE (`branch_id`, `product_id`)

### 4.2 InventoryMovement (ledger)

Replaces `state.counts` (promoter stock observations) and integrates sales-driven movements.

| Concept | Source |
|---|---|
| Table | `inventory_movements` |
| API | `POST /api/v1/inventory/counts`, `GET /api/v1/inventory/movements` |

Fields:

* `id` UUID PK
* `branch_id` UUID FK NOT NULL
* `product_id` UUID FK NOT NULL
* `movement_type` enum('sale_decrement','restock','count_observation','adjustment','transfer_out','transfer_in') NOT NULL
* `quantity_delta` integer NOT NULL — positive for inflow, negative for outflow
* `quantity_before` integer NOT NULL
* `quantity_after` integer NOT NULL
* `reference_type` text NULL — 'sale' | 'count' | 'manual_adjustment' | 'request_fulfillment'
* `reference_id` UUID NULL
* `actor_id` UUID FK → users NOT NULL
* `note` text NULL
* `created_at` timestamptz NOT NULL

Business rules (from frontend):

* A count observation with `quantity_after != quantity_before` requires a non-empty `note` (frontend equivalent: discrepancy reason).
* Promoter-submitted counts never overwrite reference inventory automatically — they create an `observation` movement with `quantity_delta = 0` but the observation value is recorded in a separate column below.

### 4.3 StockCountObservation

Replaces the frontend's `state.counts` and the prompt "Submit count".

| Concept | Source |
|---|---|
| Table | `stock_count_observations` |
| API | `POST /api/v1/inventory/counts`, `GET /api/v1/inventory/counts` |

Fields:

* `id` UUID PK
* `branch_id` UUID FK
* `product_id` UUID FK
* `observed_quantity` integer NOT NULL CHECK (>= 0)
* `reference_quantity` integer NOT NULL — what the reference stock was at observation time
* `note` text NULL — required if `observed_quantity != reference_quantity`
* `observer_id` UUID FK → users
* `created_at` timestamptz NOT NULL

The observation does NOT mutate `branch_stock.quantity`. It generates an `inventory_movement` of type `count_observation` with `quantity_delta = 0` (audit only) and stores the observed value on this table. This preserves the frontend rule: "Counts do not overwrite reference inventory."

## 5. Sales Domain

### 5.1 Sale

Replaces `DemoProvider.sales`.

| Concept | Source |
|---|---|
| Table | `sales` |
| API | `POST /api/v1/sales`, `GET /api/v1/sales`, `GET /api/v1/sales/{id}` |

Fields:

* `id` UUID PK
* `promoter_id` UUID FK → users NOT NULL — server-derived from JWT, never trusted from body
* `branch_id` UUID FK NOT NULL — server-derived from the promoter's active assignment
* `product_id` UUID FK NOT NULL — must be active
* `quantity` integer NOT NULL CHECK (1 <= quantity <= 999)
* `unit_price` numeric(12,2) NOT NULL — server-snapshotted at sale time from `products.price`
* `total_amount` numeric(14,2) NOT NULL — server-computed = `unit_price * quantity`
* `note` text NULL
* `status` enum('recorded','corrected','voided') NOT NULL DEFAULT 'recorded'
* `created_at`, `updated_at`

Business rules (from frontend):

* Quantity in 1..999.
* Product must be active.
* Server computes `total_amount` and `unit_price`. Client body values are NEVER trusted.
* Sales do NOT auto-decrement stock in v1 (the frontend explicitly labels them "reporting only" and does not touch `product.stock`). The transaction model exists in `inventory_movements` but the sale-service for v1 does not emit a movement; this is documented as a deferred decision.
* If a future business requirement adds decrement-on-sale, it must be a transactional change that also updates `branch_stock` and emits a `sale_decrement` movement.

### 5.2 SaleCorrection (audit-only)

When a sale is corrected (rare, out of scope for v1 routes but modeled for audit preservation):

| Concept | Source |
|---|---|
| Table | `sale_corrections` |

Fields:

* `id` UUID PK
* `sale_id` UUID FK
* `corrected_by` UUID FK
* `previous_quantity` int
* `previous_unit_price` numeric
* `new_quantity` int
* `new_unit_price` numeric
* `reason` text
* `created_at`

## 6. Requests Domain

### 6.1 StockRequest

Replaces `DemoProvider.requests`.

| Concept | Source |
|---|---|
| Table | `stock_requests` |
| API | `POST /api/v1/requests`, `GET /api/v1/requests`, `GET /api/v1/requests/{id}`, `POST /api/v1/requests/{id}/approve`, `POST /api/v1/requests/{id}/request-changes`, `POST /api/v1/requests/{id}/cancel` |

Fields:

* `id` UUID PK
* `requester_id` UUID FK → users NOT NULL
* `request_type` enum('restock','relocate') NOT NULL
* `product_id` UUID FK NOT NULL
* `quantity` int NOT NULL CHECK (1..9999)
* `reason` text NOT NULL CHECK (char_length(reason) >= 5)
* `destination_branch_id` UUID FK NOT NULL
* `source_branch_id` UUID FK NULL — filled in by supervisor on relocate approval
* `status` enum('pending','approved','changes_requested','cancelled','fulfilled') NOT NULL DEFAULT 'pending'
* `created_at`, `updated_at`, `decided_at`, `fulfilled_at`

State transitions:

```
pending → approved       (supervisor)
pending → changes_requested (supervisor)
pending → cancelled      (requester, before decision)
changes_requested → pending (requester, after updating reason)
approved → fulfilled     (admin or supervisor; future)
* → * is forbidden otherwise
```

Business rules (from frontend):

* Self-approval forbidden (requester cannot approve own request).
* Status mutation must use the dedicated transition routes (no PATCH on `status`).

### 6.2 RequestActivity (optional audit trail)

Out of scope for v1 routes but modeled for activity timeline:

| Concept | Source |
|---|---|
| Table | `request_activity_events` |

Fields: `id`, `request_id` FK, `actor_id` FK, `event_type`, `note`, `created_at`.

## 7. Reviews Domain

### 7.1 Review

Replaces `ManagementProvider.reviews`. Reviewable entity types: `stock_request`, `shelf_photo`.

| Concept | Source |
|---|---|
| Table | `reviews` |
| API | `POST /api/v1/reviews`, `GET /api/v1/reviews` |

Fields:

* `id` UUID PK
* `reviewer_id` UUID FK → users NOT NULL — supervisor only
* `target_type` enum('stock_request','shelf_photo') NOT NULL
* `target_id` UUID NOT NULL — polymorphic; logical FK enforced by service-layer check
* `decision` enum('approved','changes_requested') NOT NULL
* `note` text NOT NULL CHECK (char_length(note) >= 5)
* `created_at`, `updated_at`
* UNIQUE (`target_type`, `target_id`, `reviewer_id`) — only one review per reviewer per target at a time

Behavior:

* On a `changes_requested` decision against a `shelf_photo`, when the promoter later edits the photo notes, the existing review is **soft-deleted** (status field updated) and a new review is required. Mirrors the current frontend behavior in `PhotoScreens.tsx` where editing notes clears the review.

## 8. Attendance Domain

### 8.1 AttendanceShift

Replaces `DemoProvider.shifts`.

| Concept | Source |
|---|---|
| Table | `attendance_shifts` |
| API | `POST /api/v1/attendance/check-in`, `POST /api/v1/attendance/check-out`, `GET /api/v1/attendance` |

Fields:

* `id` UUID PK
* `user_id` UUID FK NOT NULL
* `branch_id` UUID FK NOT NULL — server-set from user assignment
* `started_at` timestamptz NOT NULL DEFAULT now() — server-controlled
* `ended_at` timestamptz NULL
* `duration_minutes` int GENERATED ALWAYS AS (CASE WHEN ended_at IS NULL THEN NULL ELSE (EXTRACT(EPOCH FROM (ended_at - started_at)) / 60)::int END) STORED

Constraints:

* Partial UNIQUE index `attendance_shifts_one_active_per_user` on (`user_id`) WHERE `ended_at IS NULL` — at most one active shift per user.
* `check_out` sets `ended_at = now()`.

## 9. Photos Domain

### 9.1 ShelfPhoto

Replaces `DemoProvider.photos`.

| Concept | Source |
|---|---|
| Table | `shelf_photos` |
| API | `POST /api/v1/photos` (multipart), `GET /api/v1/photos`, `GET /api/v1/photos/{id}` |

Fields:

* `id` UUID PK
* `uploader_id` UUID FK → users NOT NULL
* `branch_id` UUID FK NOT NULL
* `storage_key` text NOT NULL — object-storage path
* `mime_type` text NOT NULL
* `file_size_bytes` int NOT NULL
* `width` int NULL
* `height` int NULL
* `source` enum('camera','library') NOT NULL
* `note` text NULL
* `latitude` numeric(9,6) NULL
* `longitude` numeric(9,6) NULL
* `taken_at` timestamptz NULL — claimed capture time (NOT authoritative)
* `created_at` timestamptz NOT NULL DEFAULT now()

Binary is stored via `StorageBackend` (`local_disk` implementation in dev). Postgres only stores metadata.

## 10. Rewards Domain

### 10.1 RewardRule

Defines how points are earned.

| Concept | Source |
|---|---|
| Table | `reward_rules` |
| API | `POST /api/v1/rewards/rules` (admin), `GET /api/v1/rewards/rules` |

Fields:

* `id` UUID PK
* `code` text UNIQUE NOT NULL — 'sale_unit', 'lesson_complete', 'challenge_join', etc.
* `description` text NOT NULL
* `points_per_unit` numeric(12,2) NOT NULL
* `is_active` boolean NOT NULL DEFAULT TRUE
* `created_at`, `updated_at`

### 10.2 PointLedger

Replaces the implicit `state.sales.reduce(... * 10)` and `completedLessons.length * 20` logic in `RewardsScreens.tsx`.

| Concept | Source |
|---|---|
| Table | `point_ledger` |
| API | `GET /api/v1/rewards/me`, `GET /api/v1/rewards/ledger` |

Fields:

* `id` UUID PK
* `user_id` UUID FK NOT NULL
* `reward_rule_id` UUID FK NOT NULL
* `quantity_units` int NOT NULL DEFAULT 1 — number of units this earning represents
* `points_earned` numeric(12,2) NOT NULL — server-computed
* `reference_type` text NULL — 'sale' | 'lesson' | 'challenge'
* `reference_id` UUID NULL
* `created_at` timestamptz NOT NULL

Current rules preserved from frontend:

* `sale_unit` rule → 10 points per unit sold.
* `lesson_complete` rule → 20 points per lesson.
* Points are earned when a sale is recorded (server emits ledger entries) or when a lesson is marked complete.
* Current balance = `SUM(points_earned) - SUM(points_redeemed)` where redemption is modeled in `point_redemptions` but out of scope in v1.

### 10.3 Lesson / LessonCompletion

Replaces the hardcoded `lessons` array in `AccountScreens.tsx`.

| Concept | Source |
|---|---|
| Table | `lessons`, `lesson_completions` |

`lessons`:

* `id` UUID PK
* `code` text UNIQUE NOT NULL — 'sales_conversation', 'shelf_photo_checklist'
* `title_en` text NOT NULL
* `title_ar` text NULL
* `body_en` text NOT NULL
* `body_ar` text NULL
* `estimated_minutes` int NOT NULL DEFAULT 2
* `is_active` boolean NOT NULL DEFAULT TRUE

`lesson_completions`:

* `id` UUID PK
* `user_id` UUID FK
* `lesson_id` UUID FK
* `completed_at` timestamptz NOT NULL DEFAULT now()
* UNIQUE (`user_id`, `lesson_id`)

### 10.4 Challenge / ChallengeEnrollment

Replaces `state.joined` boolean and `/detail/challenge` screen logic.

| Concept | Source |
|---|---|
| Table | `challenges`, `challenge_enrollments` |

`challenges`:

* `id` UUID PK
* `code` text UNIQUE NOT NULL — 'ten_unit'
* `title_en` text NOT NULL
* `description_en` text NOT NULL
* `target_units` int NOT NULL — 10 for the existing challenge
* `reward_rule_id` UUID FK NULL — optional completion reward
* `is_active` boolean NOT NULL DEFAULT TRUE
* `starts_at` timestamptz NULL
* `ends_at` timestamptz NULL

`challenge_enrollments`:

* `id` UUID PK
* `user_id` UUID FK
* `challenge_id` UUID FK
* `enrolled_at` timestamptz NOT NULL DEFAULT now()
* `completed_at` timestamptz NULL — set when `SUM(sale.quantity for user within challenge window) >= target_units`
* UNIQUE (`user_id`, `challenge_id`)

### 10.5 Leaderboard (read-only view)

| Concept | Source |
|---|---|
| API | `GET /api/v1/leaderboard?scope=branch|team` |

Computed on the fly from `point_ledger` (or `sales.quantity`) with branch/team filters. No persisted leaderboard table needed.

## 11. Tasks Domain

Replaces `ManagementProvider.tasks`.

| Concept | Source |
|---|---|
| Table | `tasks` |
| API | `GET /api/v1/tasks`, `POST /api/v1/tasks`, `PATCH /api/v1/tasks/{id}`, `POST /api/v1/tasks/{id}/complete`, `POST /api/v1/tasks/{id}/reopen` |

Fields:

* `id` UUID PK
* `assignee_id` UUID FK → users NOT NULL — promoter
* `assigner_id` UUID FK → users NOT NULL — supervisor
* `title` text NOT NULL CHECK (char_length >= 4)
* `due_date` date NOT NULL — YYYY-MM-DD
* `status` enum('open','completed') NOT NULL DEFAULT 'open'
* `completed_at` timestamptz NULL
* `created_at`, `updated_at`

Business rules:

* `assignee` must be in the assigner's team (supervisor_id = assigner.id) and active.
* Only the assignee or the assigner can change status.
* Reopen requires the assigner (or admin).

## 12. Targets Domain

Replaces `ManagementProvider.targets`.

| Concept | Source |
|---|---|
| Table | `branch_targets` |
| API | `GET /api/v1/targets`, `POST /api/v1/targets` (admin), `PATCH /api/v1/targets/{id}` |

Fields:

* `id` UUID PK
* `branch_id` UUID FK NOT NULL
* `period_type` enum('daily','weekly','monthly') NOT NULL DEFAULT 'daily'
* `period_start` date NOT NULL
* `period_end` date NULL — null for open-ended recurring
* `amount` numeric(14,2) NOT NULL CHECK (amount > 0)
* `is_active` boolean NOT NULL DEFAULT TRUE
* `created_at`, `updated_at`
* UNIQUE (`branch_id`, `period_type`, `period_start`)

The promoter `Home` endpoint resolves the active target for the user's branch.

## 13. Notifications Domain

Replaces the synthetic notification list in `AccountScreens.tsx` (`NotificationsScreen`).

| Concept | Source |
|---|---|
| Table | `notifications` |
| API | `GET /api/v1/notifications`, `PATCH /api/v1/notifications/{id}/read`, `POST /api/v1/notifications/mark-all-read` |

Fields:

* `id` UUID PK
* `recipient_id` UUID FK → users NOT NULL
* `title_en` text NOT NULL
* `title_ar` text NULL
* `body_en` text NOT NULL
* `body_ar` text NULL
* `type` enum('request_status','training','challenge','system') NOT NULL
* `reference_type` text NULL — 'stock_request' | 'task' | 'challenge' | 'sale'
* `reference_id` UUID NULL
* `read_at` timestamptz NULL
* `created_at` timestamptz NOT NULL

Push delivery is out of scope; backend emits DB rows only.

## 14. Audit Domain

Replaces `ManagementProvider.audit`.

| Concept | Source |
|---|---|
| Table | `audit_events` |
| API | `GET /api/v1/audit` (admin) |

Fields:

* `id` UUID PK
* `actor_id` UUID FK → users NULL — null only for system events
* `actor_role` enum('promoter','supervisor','admin','system') NOT NULL
* `action` text NOT NULL — e.g. 'task.created', 'user.updated'
* `entity_type` text NOT NULL — e.g. 'user', 'task'
* `entity_id` UUID NULL
* `details` jsonb NOT NULL DEFAULT '{}'::jsonb
* `ip` text NULL
* `user_agent` text NULL
* `created_at` timestamptz NOT NULL DEFAULT now()

Indexed by `actor_id`, `created_at`, `entity_type`, `action`. No arbitrary 500-row cap.

## 15. Mapping Table (Concept → Domain → Table → API)

| Frontend concept | Backend domain | Table | API |
|---|---|---|---|
| `DemoProvider.profile` | Identity | `users` | `GET /auth/me`, `PATCH /users/{id}` |
| `Login` (username/password) | Identity | `users` | `POST /auth/login` |
| `Preferences` (light/dark, language) | Identity | (frontend-only) | (frontend-managed) |
| `DemoProvider.products` | Catalog | `products` | `GET/POST /products` |
| `ManagementProvider.catalog` | Catalog | `products` | `GET/POST /products` |
| `ManagementProvider.branches` | Organization | `branches` | `GET/POST /branches` |
| `ManagementProvider.staff` | Identity | `users` | `GET/POST /users` |
| `ManagementProvider.targets.b1` | Targets | `branch_targets` | `GET/POST /targets` |
| `DemoProvider.sales` | Sales | `sales` | `GET/POST /sales` |
| `DemoProvider.requests` | Requests | `stock_requests` | `GET/POST /requests`, `/requests/{id}/approve` |
| `DemoProvider.shifts` | Attendance | `attendance_shifts` | `POST /attendance/check-in`, `/check-out`, `GET /attendance` |
| `DemoProvider.photos` | Photos | `shelf_photos` | `GET/POST /photos` |
| `DemoProvider.counts` | Inventory | `stock_count_observations` + `inventory_movements` | `POST /inventory/counts` |
| `DemoProvider.notifications` flag | Notifications | `notifications` | `GET /notifications`, `/notifications/{id}/read` |
| `DemoProvider.completedLessons` | Rewards | `lesson_completions` | `POST /lessons/{id}/complete` |
| `DemoProvider.joined` | Rewards | `challenge_enrollments` | `POST /challenges/{code}/join` |
| `ManagementProvider.reviews` | Reviews | `reviews` | `GET/POST /reviews` |
| `ManagementProvider.tasks` | Tasks | `tasks` | `GET/POST /tasks` |
| `ManagementProvider.audit` | Audit | `audit_events` | `GET /audit` |
| Points from sales | Rewards | `point_ledger` | `GET /rewards/me`, `GET /rewards/ledger` |
| Leaderboard | Rewards | (computed) | `GET /leaderboard` |

## 16. State Machines (Summary)

### Sale

`recorded → corrected → voided` (rare; reserved for future correction flow)

### StockRequest

```
pending ─approve─▶ approved
        ─request_changes─▶ changes_requested ─requester_update─▶ pending
        ─cancel(requester)─▶ cancelled
approved ─fulfill─▶ fulfilled
```

### AttendanceShift

`open → closed` (irreversible via normal flow; manual reopen by admin only).

### Task

`open → completed` (assignee or assigner) → `completed → open` (assigner reopen).

### Review

Inserted once. On photo note edit, existing review is invalidated (`is_active = false`) and a new review must be created. A historical record is kept in `review_history` for auditability (optional table for v1).

### ChallengeEnrollment

`enrolled → completed` (when aggregate units reach `target_units`).

## 17. Indexes (Initial)

* `users(email)` UNIQUE
* `users(role)`, `users(branch_id)`, `users(supervisor_id)`
* `branches(code)` UNIQUE, `branches(is_active)`
* `products(sku)` UNIQUE, `products(is_active)`
* `branch_stock(branch_id, product_id)` UNIQUE
* `inventory_movements(branch_id, product_id, created_at)`
* `stock_count_observations(branch_id, product_id, created_at)`
* `sales(promoter_id, created_at)`, `sales(branch_id, created_at)`
* `stock_requests(requester_id, status)`, `stock_requests(status, created_at)`
* `reviews(target_type, target_id)`
* `attendance_shifts(user_id, started_at DESC)` partial WHERE `ended_at IS NULL`
* `shelf_photos(uploader_id, created_at)`, `shelf_photos(branch_id, created_at)`
* `point_ledger(user_id, created_at)`
* `notifications(recipient_id, read_at, created_at)`
* `tasks(assignee_id, status, due_date)`
* `branch_targets(branch_id, period_type, period_start)` UNIQUE
* `audit_events(created_at DESC)`, `audit_events(actor_id, created_at DESC)`, `audit_events(entity_type, entity_id)`