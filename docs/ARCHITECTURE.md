# VOLTEX architecture

## Current scope

Expo SDK 57 / React Native 0.86.3 / React 19.2.3 / TypeScript, Android and iOS. All 25 named promoter destinations have frontend implementations. See `SCREEN_MAP.md` for the route/action inventory and `RESEARCH.md` for research. App Shell is a navigation container, not an extra business screen.

The explicit demo action on Login opens a role picker without claiming authentication. All three roles now have frontend workspaces: the original 25 promoter pages plus 9 supervisor pages and 13 admin pages. Reviews and administration are local demo workflows, not server actions. See `MANAGEMENT.md` for routes, shared interactions and boundaries.

## Boundaries

- `app`: launch routes, five tabs, 12 explicit detail files and five explicit modal-form files, each bound directly to its feature screen. There is no `[screen]` dispatcher: `screen` is reserved by the navigation system. All 17 internal files are explicitly registered in the root stack. SDK 57 uses `expo-router/js-tabs`. Unknown external URLs and rendering failures retain recovery UI.
- `src/features/auth`: login form and localized copy. Passwords exist only in component state and are never logged, persisted, or transmitted in this phase.
- `src/theme`: shared semantic colors, English/Arabic choice, Light/Dark/System preference. Only these display preferences are saved to AsyncStorage.
- `src/components`: native SVG icons and reconstructed brand mark.
- `src/components/ui.tsx`: semantic cards, inputs, labels, progress, list actions and keyboard/safe-area-aware page shells.
- `src/features/sales`, `stock`, `rewards`, `operations`, `account`, `dashboard`: screens grouped by business capability.
- `src/demo`: versioned AsyncStorage state, serialized writes, record validation, form drafts and Arabic/Persian number normalization. Replace demo access with typed repository/service operations during integration.
- `src/management`: role picker/gates, admin and supervisor screens, separate persistent state, and feedback/task components shared with the promoter. New layouts retain explicit routes and SDK 57 JS tabs.
- `assets/voltex-logo.svg`: standalone vector logo. The mark is redrawn from the supplied image, not an original brand asset; exact brand geometry and tagline font require the original artwork.

## Next backend phase

Use Supabase Auth, PostgreSQL, private object storage, and server-side operations for privileged mutations. Roles: admin, supervisor, promoter. No Ads role. Starting assumption: one organization with multiple branches; confirm before database migrations.

Model profiles, branches, staff assignments, supervisor team assignments, products, sales and sale items, stock counts, attendance, shelf photos, requests, targets, rewards, notifications and audit events. Design foreign keys and record ownership before API implementation. Decide whether sales affect inventory and how offline submissions are reconciled before shipping those modules.

Enforce permissions in the backend and database, never only in navigation. Promoters access their permitted records and assigned branches; supervisors access assigned teams and branches; admins perform authorized management actions. Users cannot edit their own roles or assignments. Privileged service credentials must never be included in the app.

Introduce an auth service with sign-in, sign-out, session restore and recovery after choosing the identity scheme. The reference uses a username; decide how it maps to the authentication provider without exposing account lookup. Remember me controls secure session persistence after integration; it currently only changes form state. Store session credentials in secure platform storage, not AsyncStorage. Biometrics should unlock an existing valid session after enrollment, with capability checks and a password fallback. Do not equate biometric device unlock with employee attendance verification.

## UI behavior

Light/English preserve the login reference by default. Every new static screen string has English/Arabic alternatives; user content is unchanged. The eye and field validation work locally. Recovery is a form preview, not an email sender. Biometrics explain enrollment requirements. The explicit demo action is separate from account login.

Sales, requests, counts, shifts, photo metadata, profile edits, read markers, lesson completion and challenge enrollment share persistent local state. Sales/count/request drafts survive navigation. Derived dashboards, points and lists update together. Duplicate submit taps are guarded; only one demo shift is open at a time. Reference stock is not overwritten by sales reports or count observations.

Photos are copied to app documents. Camera/library selection and optional current-location attachment occur only on user action. Photo detail allows note edits and confirmed removal of the app-owned copy. Location failures time out; no background tracking, verified capture location or automatic compliance score is claimed. The file, metadata and state paths are separated for later upload integration.

Products, prices, participants, branch assignments, target and reward rules are illustrative. There are no real server approvals, push subscriptions or inventory adjustments. Passwords never enter local demo storage. E/X spacing is corrected in both SVG variants.

## Verification still required (when execution is authorized)

SDK 57 packages, node_modules and a lockfile were already present when the user confirmed the SDK. Their manifests were read without executing them; the agent did not install or run them. Source and route review is recorded in `FRONTEND_AUDIT.md`. No compiler, test runner, app, build, screenshot renderer or simulator was started.

After execution is authorized, run TypeScript checks and review Android/iOS, compact displays, tablets, keyboard, accessibility text, VoiceOver/TalkBack, theme restoration, Arabic, autofill and native camera/GPS. Visual and runtime correctness cannot be certified as 100% from source review alone.
