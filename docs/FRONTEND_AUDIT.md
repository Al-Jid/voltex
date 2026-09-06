# Frontend source review — 6 September 2026

## New role workspaces

The user subsequently confirmed that the corrected promoter navigation worked without errors on Expo Go 57. The agent then added 9 supervisor routes, 13 admin routes and a demo role picker. See `MANAGEMENT.md` for the complete scope and source-review status. Earlier statements below about management pages being out of scope apply to the previous promoter-only delivery. No runtime tests were performed for the new additions.

## Navigation correction after user-reported Page not found

The earlier source coverage conclusion did not establish that navigation worked. The two dynamic `[screen]` dispatchers used a reserved navigation parameter. This was a concrete design defect and was missed in the earlier source review; the user reported internal pages displaying Page not found.

Both dispatcher files are now removed. Every one of the 12 detail destinations and five forms has its own concrete route file and root-stack registration. Existing button URLs are preserved. No regular internal page renders a generic Page not found dispatcher. Sale/request detail URLs without an ID show a usable record picker; stale IDs offer recovery instead of inventing records. The global not-found page remains only for genuinely unknown URLs.

Reference: [Expo reserved URL parameters](https://docs.expo.dev/router/reference/url-parameters/). `screen`, `params`, `initial` and `state` are reserved for navigation internals.

This correction was reviewed from source, without running the application. It removes the identified collision; runtime confirmation remains outstanding. The earlier registry-based review entries below are historical and superseded by these explicit route files.

## Conclusion

All **25 named promoter destinations** are represented in source with route entry points and UI content. The route inventory covers **3 launch/auth pages + 5 tab roots + 12 detail destinations + 5 modal forms = 25**. Forgot Password is one of the five forms. Supplemental dialogs, expandable content and error recovery do not inflate the screen count.

This is **source coverage**, not a passing runtime/visual test result and not a 100% bug-free certification.

## Evidence inspected

| Area | Source evidence and result |
|---|---|
| SDK | `package.json`, installed `expo/package.json`, installed bundled-native-module table: Expo 57.0.20, React 19.2.3, React Native 0.86.3. Declared native packages match the SDK 57 table. User's package/lock/config edits retained. |
| Routing | Root stack, five files under `(tabs)`, detail registry with 12 keys, form registry with five keys. Each registered component has an implementation. Link targets reviewed against the registries. |
| SDK navigation entry | JS tabs import updated to `expo-router/js-tabs` based on installed SDK 57 declarations; the old root export is deprecated. |
| Login/launch | Reference login retained, logo spacing repaired, three introduction slides, explicit demo entry; real login/biometrics not simulated. |
| Sales | Search/period filters, amount calculation, integer validation, double-submit guard, persistent draft, local save → detail → list; shared data drives dashboard and rewards. |
| Stock | Filters, count observation, zero support, discrepancy reason, count history and notes, restock prefill; source inventory remains unchanged. |
| Attendance | Confirmed local start/end, single-open-shift guard, history and duration. No real attendance/geofence claim. |
| Requests | Typed creation, reason/quantity validation, persistent draft, linked detail, confirmed cancellation, status filters and linked notifications. |
| Photos | Camera/library selection, explicit permissions, cancellation/error paths, optional foreground location with timeout, app-documents copy, source/date/notes, full detail modal, note updates and confirmed deletion of local copy. |
| Rewards/training | Derived units/points, enrollment, completion progress, branch/team ranking, expandable readable lessons and completion controls. |
| Account | Profile validation and hydration refresh, role/assignment read-only, read/unread notifications, reminder toggle, persistent language/theme. |
| Layout | Shared tokens, scroll/keyboard page shell, safe-area spacing, 44-point controls, Arabic row/text direction, FAB hidden with keyboard; onboarding now scrolls on compact screens. |
| Fallbacks | Empty lists, missing records/images, unknown routes and provider-independent rendering error recovery UI. Registry lookup rejects prototype properties. |
| Data | Versioned record shape checks, serialized local writes, storage failure banner. Credentials are not logged or stored in demo state. |

## Corrections from source review

- Preserved the user's SDK 57 update; removed obsolete documentation describing SDK 55/login-only scope.
- Changed the deprecated tab import to the SDK 57 JS-tabs entry point.
- Added safe scrolling to onboarding and space around the floating action button.
- Made profile fields refresh after stored data hydration.
- Added bilingual SKU search and Arabic/Persian integer normalization.
- Added guarded registry lookup and error recovery routes.
- Added location timeout and photo detail/edit/removal flow.
- Exposed complete count history, including discrepancy notes.
- Moved X away from E in both SVG versions.

## Explicit remaining integration work

Real accounts/recovery/biometrics, server authorization, real inventory/catalog/prices, supervisor approvals, validated attendance/GPS, photo upload/compliance review, reward policy, push notifications and offline synchronization. The three planned roles are unchanged; administrator/supervisor screens are outside this promoter sitemap.

## Checks not performed

No app start, dependency installation by the agent, typecheck, lint, automated tests, native build, simulator, device test or screenshot comparison. Existing node_modules/lockfile were read, not executed. Device UI, native permissions and platform behavior need the manual scenarios in `SCREEN_MAP.md` when execution is allowed. Commands in README are instructions for the user, not evidence of tests having run.
