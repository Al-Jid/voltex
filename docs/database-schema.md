# VOLTEX Database Schema (PostgreSQL)

This document is the source of truth for the relational schema. The Alembic migration in `backend/migrations/versions/0001_initial.py` must match this document exactly.

## Conventions

* Primary keys: `UUID` (Postgres `uuid` type), generated server-side via `gen_random_uuid()` (extension `pgcrypto`).
* Timestamps: `TIMESTAMPTZ` with UTC normalization. Defaults via `now()`.
* Currency: `NUMERIC(12,2)` for unit amounts; `NUMERIC(14,2)` for totals.
* Soft deletion: `is_active BOOLEAN` on `users`, `branches`, `products`, `reviews`. No cascading deletes for historical records (`sales`, `attendance_shifts`, `audit_events`, `point_ledger`).
* IDs are immutable UUIDs; do not expose sequential IDs.

## Extensions

```sql
CREATE EXTENSION IF NOT EXISTS "pgcrypto";  -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "citext";    -- case-insensitive email
```

## Enumerated Types

```sql
CREATE TYPE user_role AS ENUM ('promoter', 'supervisor', 'admin');

CREATE TYPE request_status AS ENUM (
  'pending',
  'approved',
  'changes_requested',
  'cancelled',
  'fulfilled'
);

CREATE TYPE request_type AS ENUM ('restock', 'relocate');

CREATE TYPE review_decision AS ENUM ('approved', 'changes_requested');

CREATE TYPE review_target_type AS ENUM ('stock_request', 'shelf_photo');

CREATE TYPE inventory_movement_type AS ENUM (
  'sale_decrement',
  'restock',
  'count_observation',
  'adjustment',
  'transfer_out',
  'transfer_in'
);

CREATE TYPE sale_status AS ENUM ('recorded', 'cancelled');

CREATE TYPE photo_source AS ENUM ('camera', 'library');

CREATE TYPE task_status AS ENUM ('open', 'completed');

CREATE TYPE target_period_type AS ENUM ('daily', 'weekly', 'monthly');

CREATE TYPE notification_type AS ENUM (
  'request_status',
  'training',
  'challenge',
  'system'
);

CREATE TYPE audit_actor AS ENUM ('promoter', 'supervisor', 'admin', 'system');

CREATE TYPE reward_reference_type AS ENUM ('sale', 'lesson', 'challenge', 'manual');
```

## Tables

### users

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK DEFAULT gen_random_uuid() |
| email | citext | UNIQUE NOT NULL |
| display_name | text | NOT NULL CHECK (char_length(display_name) BETWEEN 2 AND 60) |
| phone | text | NULL CHECK (char_length(phone) <= 20) |
| password_hash | text | NOT NULL |
| role | user_role | NOT NULL |
| branch_id | uuid | NOT NULL FK → branches(id) ON DELETE RESTRICT |
| supervisor_id | uuid | NULL FK → users(id) ON DELETE SET NULL |
| is_active | boolean | NOT NULL DEFAULT TRUE |
| must_change_password | boolean | NOT NULL DEFAULT FALSE |
| last_login_at | timestamptz | NULL |
| created_at | timestamptz | NOT NULL DEFAULT now() |
| updated_at | timestamptz | NOT NULL DEFAULT now() |

Check:

* `supervisor_id IS NULL OR EXISTS (SELECT 1 FROM users u WHERE u.id = supervisor_id AND u.role = 'supervisor')`

Indexes:

* `users_email_unique` UNIQUE(email)
* `users_role_idx` (role)
* `users_branch_idx` (branch_id)
* `users_supervisor_idx` (supervisor_id)
* `users_active_idx` (is_active)

### refresh_tokens

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK DEFAULT gen_random_uuid() |
| user_id | uuid | NOT NULL FK → users(id) ON DELETE CASCADE |
| token_hash | text | UNIQUE NOT NULL |
| issued_at | timestamptz | NOT NULL DEFAULT now() |
| expires_at | timestamptz | NOT NULL |
| revoked_at | timestamptz | NULL |
| replaced_by_id | uuid | NULL FK → refresh_tokens(id) |
| user_agent | text | NULL |
| ip | text | NULL |

Indexes: `refresh_user_idx` (user_id), `refresh_expires_idx` (expires_at).

### idempotency_keys

| Column | Type | Constraints |
|---|---|---|
| key | text | PK |
| user_id | uuid | NOT NULL FK → users(id) ON DELETE CASCADE |
| endpoint | text | NOT NULL |
| request_fingerprint | text | NOT NULL |
| response_status | int | NULL |
| response_body | jsonb | NULL |
| created_at | timestamptz | NOT NULL DEFAULT now() |
| expires_at | timestamptz | NOT NULL |

### branches

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK DEFAULT gen_random_uuid() |
| code | text | UNIQUE NOT NULL CHECK (char_length(code) BETWEEN 2 AND 32) |
| name | text | UNIQUE NOT NULL CHECK (char_length(name) BETWEEN 2 AND 80) |
| address | text | NULL |
| is_active | boolean | NOT NULL DEFAULT TRUE |
| created_at | timestamptz | NOT NULL DEFAULT now() |
| updated_at | timestamptz | NOT NULL DEFAULT now() |

### products

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK DEFAULT gen_random_uuid() |
| sku | text | UNIQUE NOT NULL CHECK (sku ~ '^[A-Z0-9-]{2,30}$') |
| name | text | NOT NULL CHECK (char_length(name) BETWEEN 2 AND 80) |
| name_ar | text | NULL |
| description | text | NULL |
| price | numeric(12,2) | NOT NULL CHECK (price >= 0) |
| daily_target | int | NULL CHECK (daily_target IS NULL OR daily_target >= 0) |
| is_active | boolean | NOT NULL DEFAULT TRUE |
| created_at | timestamptz | NOT NULL DEFAULT now() |
| updated_at | timestamptz | NOT NULL DEFAULT now() |

### branch_stock

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK DEFAULT gen_random_uuid() |
| branch_id | uuid | NOT NULL FK → branches(id) ON DELETE RESTRICT |
| product_id | uuid | NOT NULL FK → products(id) ON DELETE RESTRICT |
| quantity | int | NOT NULL DEFAULT 0 CHECK (quantity >= 0) |
| updated_at | timestamptz | NOT NULL DEFAULT now() |
| | | UNIQUE(branch_id, product_id) |

### inventory_movements

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK DEFAULT gen_random_uuid() |
| branch_id | uuid | NOT NULL FK → branches(id) ON DELETE RESTRICT |
| product_id | uuid | NOT NULL FK → products(id) ON DELETE RESTRICT |
| movement_type | inventory_movement_type | NOT NULL |
| quantity_delta | int | NOT NULL |
| quantity_before | int | NOT NULL |
| quantity_after | int | NOT NULL |
| reference_type | text | NULL |
| reference_id | uuid | NULL |
| actor_id | uuid | NOT NULL FK → users(id) ON DELETE RESTRICT |
| note | text | NULL |
| created_at | timestamptz | NOT NULL DEFAULT now() |

Check: `quantity_after = quantity_before + quantity_delta`.

### stock_count_observations

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK DEFAULT gen_random_uuid() |
| branch_id | uuid | NOT NULL FK → branches(id) ON DELETE RESTRICT |
| product_id | uuid | NOT NULL FK → products(id) ON DELETE RESTRICT |
| observed_quantity | int | NOT NULL CHECK (observed_quantity >= 0 AND observed_quantity <= 99999) |
| reference_quantity | int | NOT NULL |
| note | text | NOT NULL CHECK (char_length(note) >= 5) |
| observer_id | uuid | NOT NULL FK → users(id) ON DELETE RESTRICT |
| created_at | timestamptz | NOT NULL DEFAULT now() |

Check: `observed_quantity <> reference_quantity OR char_length(note) >= 5` (mirrors frontend: discrepancy requires explanation).

### sales

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK DEFAULT gen_random_uuid() |
| promoter_id | uuid | NOT NULL FK → users(id) ON DELETE RESTRICT |
| branch_id | uuid | NOT NULL FK → branches(id) ON DELETE RESTRICT |
| product_id | uuid | NOT NULL FK → products(id) ON DELETE RESTRICT |
| quantity | int | NOT NULL CHECK (quantity BETWEEN 1 AND 999) |
| unit_price | numeric(12,2) | NOT NULL CHECK (unit_price >= 0) |
| total_amount | numeric(14,2) | NOT NULL CHECK (total_amount >= 0) |
| note | text | NULL CHECK (char_length(note) <= 500) |
| status | sale_status | NOT NULL DEFAULT 'recorded' |
| created_at | timestamptz | NOT NULL DEFAULT now() |
| updated_at | timestamptz | NOT NULL DEFAULT now() |

Check: `total_amount = unit_price * quantity`.

### stock_requests

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK DEFAULT gen_random_uuid() |
| requester_id | uuid | NOT NULL FK → users(id) ON DELETE RESTRICT |
| request_type | request_type | NOT NULL |
| product_id | uuid | NOT NULL FK → products(id) ON DELETE RESTRICT |
| quantity | int | NOT NULL CHECK (quantity BETWEEN 1 AND 9999) |
| reason | text | NOT NULL CHECK (char_length(reason) >= 5 AND char_length(reason) <= 500) |
| destination_branch_id | uuid | NOT NULL FK → branches(id) ON DELETE RESTRICT |
| source_branch_id | uuid | NULL FK → branches(id) ON DELETE RESTRICT |
| status | request_status | NOT NULL DEFAULT 'pending' |
| decided_at | timestamptz | NULL |
| fulfilled_at | timestamptz | NULL |
| created_at | timestamptz | NOT NULL DEFAULT now() |
| updated_at | timestamptz | NOT NULL DEFAULT now() |

Check:

* `(request_type <> 'relocate' OR source_branch_id IS NULL OR source_branch_id <> destination_branch_id)`
* `decided_at IS NULL OR status IN ('approved','changes_requested','cancelled','fulfilled')`

### reviews

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK DEFAULT gen_random_uuid() |
| reviewer_id | uuid | NOT NULL FK → users(id) ON DELETE RESTRICT |
| target_type | review_target_type | NOT NULL |
| target_id | uuid | NOT NULL |
| decision | review_decision | NOT NULL |
| note | text | NOT NULL CHECK (char_length(note) >= 5) |
| is_active | boolean | NOT NULL DEFAULT TRUE |
| created_at | timestamptz | NOT NULL DEFAULT now() |
| updated_at | timestamptz | NOT NULL DEFAULT now() |
| | | UNIQUE(reviewer_id, target_type, target_id) |

Logical FKs:

* `target_type = 'stock_request'` ⇒ `target_id` MUST exist in `stock_requests.id`
* `target_type = 'shelf_photo'` ⇒ `target_id` MUST exist in `shelf_photos.id`

Enforced in service layer (no SQL FK to allow polymorphism).

### attendance_shifts

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK DEFAULT gen_random_uuid() |
| user_id | uuid | NOT NULL FK → users(id) ON DELETE RESTRICT |
| branch_id | uuid | NOT NULL FK → branches(id) ON DELETE RESTRICT |
| started_at | timestamptz | NOT NULL DEFAULT now() |
| ended_at | timestamptz | NULL |
| duration_minutes | int | GENERATED ALWAYS AS (CASE WHEN ended_at IS NULL THEN NULL ELSE (EXTRACT(EPOCH FROM (ended_at - started_at)) / 60)::int END) STORED |

Partial unique index:

* `attendance_one_active_per_user` UNIQUE(user_id) WHERE ended_at IS NULL

### shelf_photos

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK DEFAULT gen_random_uuid() |
| uploader_id | uuid | NOT NULL FK → users(id) ON DELETE RESTRICT |
| branch_id | uuid | NOT NULL FK → branches(id) ON DELETE RESTRICT |
| storage_key | text | NOT NULL |
| mime_type | text | NOT NULL CHECK (mime_type ~ '^image/') |
| file_size_bytes | int | NOT NULL CHECK (file_size_bytes > 0 AND file_size_bytes <= 20 * 1024 * 1024) |
| width | int | NULL |
| height | int | NULL |
| source | photo_source | NOT NULL |
| note | text | NULL CHECK (char_length(note) <= 500) |
| latitude | numeric(9,6) | NULL CHECK (latitude IS NULL OR (latitude BETWEEN -90 AND 90)) |
| longitude | numeric(9,6) | NULL CHECK (longitude IS NULL OR (longitude BETWEEN -180 AND 180)) |
| taken_at | timestamptz | NULL |
| created_at | timestamptz | NOT NULL DEFAULT now() |

### reward_rules

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK DEFAULT gen_random_uuid() |
| code | text | UNIQUE NOT NULL |
| description | text | NOT NULL |
| points_per_unit | numeric(12,2) | NOT NULL CHECK (points_per_unit >= 0) |
| is_active | boolean | NOT NULL DEFAULT TRUE |
| created_at | timestamptz | NOT NULL DEFAULT now() |
| updated_at | timestamptz | NOT NULL DEFAULT now() |

### point_ledger

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK DEFAULT gen_random_uuid() |
| user_id | uuid | NOT NULL FK → users(id) ON DELETE RESTRICT |
| reward_rule_id | uuid | NOT NULL FK → reward_rules(id) ON DELETE RESTRICT |
| quantity_units | int | NOT NULL DEFAULT 1 CHECK (quantity_units >= 1) |
| points_earned | numeric(12,2) | NOT NULL CHECK (points_earned >= 0) |
| reference_type | reward_reference_type | NULL |
| reference_id | uuid | NULL |
| created_at | timestamptz | NOT NULL DEFAULT now() |

### lessons

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK DEFAULT gen_random_uuid() |
| code | text | UNIQUE NOT NULL |
| title_en | text | NOT NULL |
| title_ar | text | NULL |
| body_en | text | NOT NULL |
| body_ar | text | NULL |
| estimated_minutes | int | NOT NULL DEFAULT 2 |
| is_active | boolean | NOT NULL DEFAULT TRUE |
| created_at | timestamptz | NOT NULL DEFAULT now() |

### lesson_completions

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK DEFAULT gen_random_uuid() |
| user_id | uuid | NOT NULL FK → users(id) ON DELETE CASCADE |
| lesson_id | uuid | NOT NULL FK → lessons(id) ON DELETE CASCADE |
| completed_at | timestamptz | NOT NULL DEFAULT now() |
| | | UNIQUE(user_id, lesson_id) |

### challenges

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK DEFAULT gen_random_uuid() |
| code | text | UNIQUE NOT NULL |
| title_en | text | NOT NULL |
| description_en | text | NOT NULL |
| target_units | int | NOT NULL CHECK (target_units > 0) |
| reward_rule_id | uuid | NULL FK → reward_rules(id) ON DELETE SET NULL |
| is_active | boolean | NOT NULL DEFAULT TRUE |
| starts_at | timestamptz | NULL |
| ends_at | timestamptz | NULL |
| created_at | timestamptz | NOT NULL DEFAULT now() |

### challenge_enrollments

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK DEFAULT gen_random_uuid() |
| user_id | uuid | NOT NULL FK → users(id) ON DELETE CASCADE |
| challenge_id | uuid | NOT NULL FK → challenges(id) ON DELETE CASCADE |
| enrolled_at | timestamptz | NOT NULL DEFAULT now() |
| completed_at | timestamptz | NULL |
| | | UNIQUE(user_id, challenge_id) |

### tasks

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK DEFAULT gen_random_uuid() |
| assignee_id | uuid | NOT NULL FK → users(id) ON DELETE RESTRICT |
| assigner_id | uuid | NOT NULL FK → users(id) ON DELETE RESTRICT |
| title | text | NOT NULL CHECK (char_length(title) BETWEEN 4 AND 160) |
| due_date | date | NOT NULL |
| status | task_status | NOT NULL DEFAULT 'open' |
| completed_at | timestamptz | NULL |
| created_at | timestamptz | NOT NULL DEFAULT now() |
| updated_at | timestamptz | NOT NULL DEFAULT now() |

Check: `assignee_id <> assigner_id`.

### branch_targets

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK DEFAULT gen_random_uuid() |
| branch_id | uuid | NOT NULL FK → branches(id) ON DELETE RESTRICT |
| period_type | target_period_type | NOT NULL DEFAULT 'daily' |
| period_start | date | NOT NULL |
| period_end | date | NULL CHECK (period_end IS NULL OR period_end >= period_start) |
| amount | numeric(14,2) | NOT NULL CHECK (amount > 0 AND amount <= 100000000) |
| is_active | boolean | NOT NULL DEFAULT TRUE |
| created_at | timestamptz | NOT NULL DEFAULT now() |
| updated_at | timestamptz | NOT NULL DEFAULT now() |
| | | UNIQUE(branch_id, period_type, period_start) |

### notifications

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK DEFAULT gen_random_uuid() |
| recipient_id | uuid | NOT NULL FK → users(id) ON DELETE CASCADE |
| title_en | text | NOT NULL |
| title_ar | text | NULL |
| body_en | text | NOT NULL |
| body_ar | text | NULL |
| type | notification_type | NOT NULL |
| reference_type | text | NULL |
| reference_id | uuid | NULL |
| read_at | timestamptz | NULL |
| created_at | timestamptz | NOT NULL DEFAULT now() |

### audit_events

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK DEFAULT gen_random_uuid() |
| actor_id | uuid | NULL FK → users(id) ON DELETE SET NULL |
| actor_role | audit_actor | NOT NULL |
| action | text | NOT NULL |
| entity_type | text | NOT NULL |
| entity_id | uuid | NULL |
| details | jsonb | NOT NULL DEFAULT '{}'::jsonb |
| ip | text | NULL |
| user_agent | text | NULL |
| created_at | timestamptz | NOT NULL DEFAULT now() |

## Entity-Relationship Summary

```
branches 1 ──< users (branch_id)
users 1 ──< users (supervisor_id)
users 1 ──< sales (promoter_id)
branches 1 ──< sales (branch_id)
products 1 ──< sales (product_id)
branches 1 ──< branch_stock (branch_id)
products 1 ──< branch_stock (product_id)
branches 1 ──< inventory_movements
products 1 ──< inventory_movements
users 1 ──< inventory_movements (actor_id)
users 1 ──< stock_count_observations (observer_id)
branches 1 ──< stock_count_observations
products 1 ──< stock_count_observations
users 1 ──< stock_requests (requester_id)
branches 1 ──< stock_requests (destination_branch_id)
branches 1 ──< stock_requests (source_branch_id)
products 1 ──< stock_requests
users 1 ──< reviews (reviewer_id)
stock_requests 1 ──< reviews (logical, target_type='stock_request')
shelf_photos 1 ──< reviews (logical, target_type='shelf_photo')
users 1 ──< attendance_shifts
branches 1 ──< attendance_shifts
users 1 ──< shelf_photos (uploader_id)
branches 1 ──< shelf_photos
reward_rules 1 ──< point_ledger
users 1 ──< point_ledger
lessons 1 ──< lesson_completions
users 1 ──< lesson_completions
challenges 1 ──< challenge_enrollments
users 1 ──< challenge_enrollments
reward_rules 1 ──< challenges (reward_rule_id)
users 1 ──< tasks (assignee_id)
users 1 ──< tasks (assigner_id)
branches 1 ──< branch_targets
users 1 ──< notifications (recipient_id)
users 1 ──< audit_events (actor_id)
users 1 ──< refresh_tokens
users 1 ──< idempotency_keys
```

## Initial Seed Data (Deterministic)

Seeded by `backend/scripts/seed.py` using FIXED UUIDs so they can be referenced in tests.

* 1 branch: `b1-citystars`
* 3 branches in v1: Citystars, Cairo Festival City, Mall of Arabia
* 1 supervisor: `s1-ahmed`
* 1 promoter: `u1-hassan`
* 4 products from frontend demo seed (`p1`–`p4`)
* Default `sale_unit` reward rule (10 points/unit), `lesson_complete` rule (20 points/lesson)
* Lessons: `sales_conversation`, `shelf_photo_checklist`
* Challenge: `ten_unit` (target 10 units)
* Branch targets: Citystars 75000 EGP/day, Cairo Festival City 60000, Mall of Arabia 50000

All seed UUIDs are deterministic and declared in `backend/scripts/seed.py`.

## Migration Strategy

* One initial migration `0001_initial.py` creates all tables, types, indexes, and extensions.
* Future migrations extend without destructive changes.
* Soft deactivation (`is_active`) for users/branches/products; no `DROP` in normal lifecycle.
* `alembic upgrade head` brings the database to the latest schema.
* `alembic downgrade -1` rolls back one migration.