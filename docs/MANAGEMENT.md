# Supervisor and Admin frontend

The original 25 promoter pages remain. Added **9 supervisor pages, 13 admin pages, and one demo role picker**. All routes are concrete files. Both roles have their own five-tab navigator using the installed Expo SDK 57 JS-tabs API. No dependencies were added or executed.

## Entry

Login → Explore demo without an account → choose a role. More also offers switching. This is UI preview selection, not authentication. The selected role is not persisted as an account claim. A cold-start management URL returns to role selection. Background layouts do not redirect during switching unless focused.

## Supervisor routes

| Route | Behavior |
|---|---|
| `/supervisor/home` | Assigned team overview, pending reviews, linked sales, shortcuts. |
| `/supervisor/team` | Search, active filter; only promoters assigned to s1. |
| `/supervisor/member?id=…` | Details, linked sales/attendance for u1, task list/completion/reopening; scope recovery. |
| `/supervisor/reviews` | Pending/reviewed request/photo queue. |
| `/supervisor/review?id=…&kind=request` or `kind=photo` | Content, approve/request changes, notes/confirmation, prior decision, missing-image handling. |
| `/supervisor/task?id=…` | Active team member, title, validated due date; save and return to member. |
| `/supervisor/reports` | Today/month, linked totals and member drill-down. |
| `/supervisor/more` | Tasks, reviews, appearance/language, guide, switch/leave. |
| `/supervisor/help` | Workflow guide and demo boundaries. |

## Admin routes

| Route | Behavior |
|---|---|
| `/admin/home` | Organization counts, creation/report/audit shortcuts. |
| `/admin/users` | Search, role filters, account status, create/edit. |
| `/admin/user?id=…` | Directory account, unique email, role/branch/supervisor/activation; validation. |
| `/admin/branches` | Search, assigned counts, create/edit. |
| `/admin/branch?id=…` | Name/address/activation, account drill-down, active-staff guard. |
| `/admin/catalog` | Planning catalog search, prices/status, add/edit. |
| `/admin/product?id=…` | Unique SKU, name, positive whole-EGP price, archive/reactivate. |
| `/admin/targets` | Daily branch targets; Citystars updates promoter Home. |
| `/admin/reports` | Branch selector, account/target data; linked Citystars transactions; empty states for others. |
| `/admin/audit` | Latest 500 local events, actor filter and timestamps. |
| `/admin/access` | Read-only intended permission model. |
| `/admin/more` | Targets/reports/audit/access/settings/guide and role switching. |
| `/admin/help` | Guide and limitations. |

Editor without id creates a record; invalid supplied id offers recovery rather than silently creating one.

## Connected demo workflows

- Promoter request → supervisor decision → feedback and request status visible to promoter; no stock movement.
- Promoter photo → supervisor decision → gallery feedback. Changed notes clear the old decision and reopen review.
- Supervisor task for u1 → promoter Home → completion visible to supervisor.
- Admin assignment changes update the supervisor's filtered team for editable accounts.
- Admin u1 display-name edit updates the promoter profile.
- Admin b1 target changes recalculate promoter Home progress.
- Management/task/review mutations add local audit events.

Only Hassan/u1 operational data is connected. Other members are directory samples without invented transactions or attendance.

## Persistence and boundaries

`ManagementProvider` stores staff, branches, planning catalog, reviews, tasks, targets and audit in a separate versioned AsyncStorage record. Writes are serialized. Invalid or failed reads disable persistence to preserve unread data; the UI shows storage failure. Original promoter records are not reset.

The three preview identities (u1, s1, a1) and linked Citystars assignment keep fixed role/activation/assignment. New accounts exercise role and supervisor assignment. Email/SKU/branch names must be unique. Active teams must be reassigned before a supervisor is deactivated or changes role; an active admin must remain. Branches with active staff cannot be disabled.

Catalog editing is a planning draft: publishing requires backend product IDs and historical sale-price snapshots. Directory account creation does not create Auth credentials or send invitations. Reviews, scope gates and audit are local UI behavior, not server authorization. Review decisions and request-status writes span two demo stores; the backend must make them transactional.

## Review status

The user reported successful navigation of the prior promoter version on Expo Go 57. That is user-reported evidence, not an agent device test, and does not validate these additions.

The agent reviewed SDK manifests, route files, component exports, links, filters and shared state as text. No app, installation, compiler/typecheck, lint, tests, simulator or build was run. Verify the new role routes, switching/back/cold start, invalid inputs, account assignments, review/reopen flows, tasks, targets, persistence, Arabic/themes and compact screens when execution is permitted.

Next: design real organization/branch/team membership; implement Auth and server permissions, typed APIs, transactional reviews and audit; then replace local demo stores feature by feature. The role picker must never become the authorization source.
