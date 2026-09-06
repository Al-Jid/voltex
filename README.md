# VOLTEX

React Native + Expo application for Android and iOS. First deliverable: the supplied login design with a vector logo, password visibility, form validation, remember-me control, English/Arabic, and persistent Light/Dark/System preferences.

Entry: `app/index.tsx`. Screen: `src/features/auth/LoginScreen.tsx`. Architecture and integration boundaries: `docs/ARCHITECTURE.md`.

This is a UI-only implementation. Authentication, recovery and biometric buttons explain their integration requirements; they do not create sessions. No passwords are saved. The logo is a vector reconstruction from the supplied raster, not the original brand file.

Dependencies are declared for Expo SDK 55. Installation, runtime execution, builds and tests have intentionally not been performed. Once approved for execution, install dependencies, validate the Expo dependency versions and run `npm run typecheck` before device review. A lockfile should be committed after that installation.
