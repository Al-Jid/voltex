# VOLTEX Authorization (RBAC)

## 1. Roles

* `promoter`
* `supervisor`
* `admin`

The role is stored on the `users` table and embedded in the JWT (`role` claim). It is **never** trusted from request bodies.

## 2. Layered Authorization

Authorization is enforced in two layers:

1. **Route-level**: FastAPI dependencies (`require_role`, `require_promoter`, `require_supervisor`, `require_admin`).
2. **Resource-scope**: every read/write of a specific record checks whether the caller is allowed to access it (e.g. supervisor only sees their own team's requests).

The route-level dependency is a coarse-grained gate. The resource-scope check is the fine-grained authority. Both are mandatory.

## 3. Resource Scope Rules

### Users

| Action | Promoter | Supervisor | Admin |
|---|---|---|---|
| Read | self | self |
| List | no | assigned team (read of profiles) | all |
| Create | no | no | yes |
| Update role/branch/supervisor | no | no | yes |
| Activate/deactivate | no | no | yes (with business rules) |

### Branches

| Action | Promoter | Supervisor | Admin |
|---|---|---|---|
| Read | own branch | own branch + assigned branches | all |
| Create/update | no | no | yes |

### Products / Catalog

All authenticated users can read. Admin-only writes.

### Inventory

* Promoter: read own branch + submit observations.
* Supervisor: read assigned branches.
* Admin: read/write all.

### Sales

| Action | Promoter | Supervisor | Admin |
|---|---|---|---|
| Read | own | own team | all |
| Create | yes (self only) | no | yes |
| Update | no | no | no (correction flow TBD) |

### Stock Requests

| Action | Promoter | Supervisor | Admin |
|---|---|---|---|
| Read | own | own team | all |
| Create | yes | no | yes |
| Approve / request-changes | no | yes (own team) | yes |
| Cancel | own (pending) | no | yes |
| Fulfill | no | yes (approved) | yes |

Self-approval is **never** allowed. The service layer raises `SELF_APPROVAL_FORBIDDEN`.

### Photos

| Action | Promoter | Supervisor | Admin |
|---|---|---|---|
| Upload | yes | yes | yes |
| Read | own + team (own branch) | team | all |
| Edit notes | own | no | no |
| Delete | own | no | yes |

### Attendance

| Action | Promoter | Supervisor | Admin |
|---|---|---|---|
| Check in/out | self | self | self |
| Read | own | own team | all |

### Tasks

| Action | Promoter | Supervisor | Admin |
|---|---|---|---|
| Create | no | yes (assigned team) | yes |
| Complete | own | yes (own created) | yes |
| Reopen | no | yes (own created) | yes |
| Read | own | own created + own team | all |

### Targets

* Admin-only writes.
* All roles can read (filtered to own branch for promoter/supervisor).

### Notifications

* Only the recipient reads/marks.

### Audit

* Admin-only.

## 4. Business Rules Enforced Server-Side

### Users

* `email` unique.
* Promoter must have active supervisor.
* Supervisor must be `supervisor` role and active.
* Branch must exist and be active.
* Last active admin protected.
* Supervisor with active promoters cannot be deactivated or have role changed.

### Products

* `sku` unique.
* Price `>= 0`.
* Cannot deactivate a product that is the subject of a pending request (warning, not hard block in v1).

### Sales

* Quantity `1..999`.
* Product must be active.
* Server computes total.

### Stock Requests

* Quantity `1..9999`.
* Reason `>= 5` chars.
* Self-approval forbidden.
* Status changes only via transition endpoints.

### Inventory

* Stock counts require a `note` if `observed_quantity != reference_quantity`.
* Observations never overwrite reference stock in v1 (mirror frontend rule).

### Reviews

- `note` `>= 5` chars.
- Reviewer must have team scope over the target.
- Editing photo notes invalidates existing reviews for that photo.

### Attendance

- One active shift per user (partial unique index).
- Cannot check out someone else's shift.

### Tasks

- `due_date` must be a valid `YYYY-MM-DD`.
- Title `>= 4` chars.
- Assignee must be in assigner's team.

## 5. FastAPI Dependencies

```python
require_role(*allowed_roles)
require_promoter / require_supervisor / require_admin
require_active_user
get_current_user        # returns User or 401
assert_in_team(supervisor_id, promoter_id)  # raises 403
assert_can_read_user(viewer, target_user)
assert_can_review_request(reviewer, request)
```

These dependencies are reusable across routes. No endpoint bypasses them.

## 6. Defense in Depth

* JWT validated for `iss` and `aud`.
* Token expiry strictly enforced.
* Refresh-token rotation + family-revocation on reuse.
* All password comparisons go through `verify_password` (constant-time).
* Audit log entry written for every successful mutating request that changes state.
* No role check `if user.role == 'admin'` in route handlers — always through `require_admin` dependency or service-level assertion.