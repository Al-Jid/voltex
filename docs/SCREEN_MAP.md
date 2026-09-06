# VOLTEX — 25-screen implementation map

Source: `D:/Downloads/VOLTEX_1.PDF` (one-page sitemap) and the supplied login reference. The PDF is a navigation diagram, not 25 visual mockups. New pages extend the login palette, typography, outlined inputs and soft violet surfaces.

The 25 count below includes Forgot Password. App Shell is a navigation container, not a 26th screen. The source's aggregate labels (25 screens / 18 full pages / 7 sheets) are not a one-to-one list of named modal routes; we preserve all named destinations. This implementation has five routed modal forms plus the existing language and appearance dialogs (seven modal surfaces).

| # | Screen | Route | Entry and interactions |
|---|---|---|---|
| 1 | Splash | `/` | Reads introduction flag; routes to onboarding or login. No fake auto-login. |
| 2 | Onboarding | `/onboarding` | Three illustrations and slides; next, back, skip, get started. Saves completion. |
| 3 | Login | `/login` | Reference layout, validation, eye, remember control, language/appearance dialogs; explicit demo entry. Actual login and biometrics remain integration boundaries. |
| 4 | Forgot password | `/sheet/forgot-password` | Username validation and recovery preview; no fake email; return to login. |
| 5 | Home | `/(tabs)/home` | Derived daily sales/units/target; attendance state; stock, photos, requests, training and notification links. |
| 6 | Sales | `/(tabs)/sales` | Today/week/month, bilingual product/reference search, totals, list, add, detail. Week begins Monday. |
| 7 | Log sale | `/sheet/log-sale` | Select SKU, integer quantity, notes, calculated value; local draft; validates and saves once, then opens detail. |
| 8 | Sale detail | `/detail/sale?id=…` | SKU, quantity, unit price, amount, branch, promoter, timestamp, status; native summary sharing and return to sales. |
| 9 | Stock | `/(tabs)/stock` | Search; all/low/out filters; quantities, latest counts; count and prefilled restock actions. |
| 10 | Submit count | `/sheet/submit-count?productId=…` | Product, actual count, discrepancy reason; local draft and saved observation. Does not overwrite reference inventory. |
| 11 | Rewards | `/(tabs)/rewards` | Derived sample points, badges, training and challenge links, leaderboard. |
| 12 | Leaderboard | `/detail/leaderboard` | Branch/team scope, sorted units, current user highlighted; other participants illustrative. |
| 13 | Challenge detail | `/detail/challenge` | Rules, join action, derived 10-unit progress/completion, sale entry. |
| 14 | More | `/(tabs)/more` | Profile, attendance, photos, requests, notifications, settings, help, leave demo. |
| 15 | Attendance | `/detail/attendance` | Confirm local check-in/out, active shift status, branch/schedule, history. No verified attendance claim. |
| 16 | Attendance log | `/detail/attendance-log` | Active/completed shifts, start/end, completed duration, empty state. |
| 17 | Shelf & photos | `/detail/shelf` | Guidance, local gallery, source/date/location/notes, camera entry, empty and missing-file states. |
| 18 | Capture photo | `/sheet/capture-photo` | Native camera/library, review/retake, notes, optional current-location request/removal; permission/error states; copies photos to app documents. |
| 19 | Requests | `/detail/requests` | All/pending/approved/cancelled filters, empty state, detail and new-request navigation. |
| 20 | New request | `/sheet/new-request?productId=…` | Restock/stock relocation, SKU, quantity, reason, receiving branch, persistent draft, local save. |
| 21 | Request detail | `/detail/request?id=…` | Context, local activity, status, confirmed cancellation, return to list. No self-approval. |
| 22 | Notifications | `/detail/notifications` | Request events and sample reminders; unread filter, mark-all-read, linked destinations; settings affect sample reminders. |
| 23 | Profile | `/detail/profile` | Read-only role/branch/supervisor; editable local name/phone and validation. |
| 24 | Settings | `/detail/settings` | Persistent Light/Dark/System, English/Arabic, demo reminder switch, data explanation, replay onboarding. |
| 25 | Help & training | `/detail/help` | Two readable lessons, expand/collapse, completion, reward points and FAQ. |

## Navigation and presentation

- Bottom tabs: Home → Sales → Stock → Rewards → More.
- Floating add button opens Log Sale, mirrored for Arabic and hidden with the keyboard.
- Nested pages have back navigation; invalid routes/record IDs have recoverable empty states.
- Forms are native stack modals. Language and appearance are dismissible dialogs on login.
- All new static UI strings have English and Arabic alternatives. User-entered content is preserved verbatim.
- Pages scroll and use keyboard avoidance and bottom safe-area spacing. Native permission/sharing UI follows the device language.

## Review scenarios — not executed

1. Complete onboarding, use explicit demo entry; visit all five tabs.
2. Log sale, back out before saving, reopen draft, save; inspect Home/Sales/Rewards without duplicates.
3. Submit a zero count, require a discrepancy reason; verify latest observation and unchanged reference inventory.
4. Prefill restock, save, open notification, mark read, cancel request; verify views agree.
5. Check in twice rapidly; only one active shift. Check out and inspect duration/history.
6. Deny camera/location, cancel picker, retry, select image, attach/remove location, save/relaunch.
7. Join challenge, record units, complete training; inspect points and ranking.
8. Switch Arabic and all themes, relaunch; review compact screens, keyboard and large font settings.
9. Open unknown detail IDs, empty filters and missing image files; verify recovery.
10. Review VoiceOver/TalkBack labels, states and touch targets.

No installation, typecheck, device run, screenshot comparison or build was performed under the no-run constraint. These scenarios remain required before declaring runtime readiness.
