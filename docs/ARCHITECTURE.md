# VOLTEX architecture

## Current scope

Expo SDK 55 / React Native / TypeScript, Android and iOS. The first route is a reference-driven login screen. No backend, account creation, fake sessions, biometric enrollment, or navigation into protected screens is implemented. No app, build, dependency installation, or tests were run, as requested.

## Boundaries

- `app`: Expo Router entry points; screens live in feature modules.
- `src/features/auth`: login form and localized copy. Passwords exist only in component state and are never logged, persisted, or transmitted in this phase.
- `src/theme`: shared semantic colors, English/Arabic choice, Light/Dark/System preference. Only these display preferences are saved to AsyncStorage.
- `src/components`: native SVG icons and reconstructed brand mark.
- `assets/voltex-logo.svg`: standalone vector logo. The mark is redrawn from the supplied image, not an original brand asset; exact brand geometry and tagline font require the original artwork.

## Next backend phase

Use Supabase Auth, PostgreSQL, private object storage, and server-side operations for privileged mutations. Roles: admin, supervisor, promoter. No Ads role. Starting assumption: one organization with multiple branches; confirm before database migrations.

Model profiles, branches, staff assignments, supervisor team assignments, products, sales and sale items, stock counts, attendance, shelf photos, requests, targets, rewards, notifications and audit events. Design foreign keys and record ownership before API implementation. Decide whether sales affect inventory and how offline submissions are reconciled before shipping those modules.

Enforce permissions in the backend and database, never only in navigation. Promoters access their permitted records and assigned branches; supervisors access assigned teams and branches; admins perform authorized management actions. Users cannot edit their own roles or assignments. Privileged service credentials must never be included in the app.

Introduce an auth service with sign-in, sign-out, session restore and recovery after choosing the identity scheme. The reference uses a username; decide how it maps to the authentication provider without exposing account lookup. Remember me controls secure session persistence after integration; it currently only changes form state. Store session credentials in secure platform storage, not AsyncStorage. Biometrics should unlock an existing valid session after enrollment, with capability checks and a password fallback. Do not equate biometric device unlock with employee attendance verification.

## UI behavior

Light mode and English match the reference by default. The eye toggles password visibility; empty required fields show localized errors and move input focus. The username shown in the reference is a placeholder, not a seeded account. Login with filled fields explains that authentication is not connected. Recovery and biometric controls show honest next-step guidance. Display preferences are stored locally; remember-me and entered credentials are not. Arabic uses local row/text direction without forcing a device-wide RTL restart. The screen scrolls and accommodates the keyboard; no phone frame or camera cutout is drawn into the app.

## Verification still required (when execution is authorized)

Install dependencies and produce a lockfile; run TypeScript checking. Compare on Android/iOS at the supplied reference size, compact displays, tablets, keyboard open and large accessibility text. Review VoiceOver/TalkBack focus, all appearance modes, preference restoration, Arabic layout, form errors and password autofill. Native Face ID testing will require a development build once authentication is implemented.
