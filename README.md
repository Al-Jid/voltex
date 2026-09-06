# VOLTEX

React Native + Expo SDK 57 for Android and iOS. A 25-screen interactive promoter prototype, following the supplied sitemap and violet login theme.

Supervisor and Admin workspaces are now included: **9 supervisor pages + 13 admin pages**, with a demo role picker. See [management routes and behavior](docs/MANAGEMENT.md). Choose a role through **Explore demo without an account**, or switch from any More tab. These new pages have source review only; the agent has not run them.

Entry: `app/index.tsx`. Complete coverage: [screen map](docs/SCREEN_MAP.md). Read the [architecture](docs/ARCHITECTURE.md), [research](docs/RESEARCH.md) and [source review](docs/FRONTEND_AUDIT.md).

Use **Explore demo without an account** on Login. Local sales, inventory observations, requests, shifts, photos, profile edits, notifications and training are interactive. Real authentication, recovery delivery, biometrics, server review, push and synchronization remain unconnected. No passwords are saved. The vector logo has corrected E/X spacing.

The agent has not run the app, compiler, tests or builds. Existing SDK 57 manifests and user-installed packages were inspected as text. Device behavior and visual fidelity remain unverified.

Internal navigation now uses 17 explicit route files instead of dynamic `[screen]` dispatchers. If an existing Expo session still holds the old route tree, restart Metro with the clear-cache command below and reopen the app.

## CMD instructions for the user (not executed by the agent)

Open CMD with Node.js available, then:

```cmd
cd /d I:\Projects\Voltex
npm install
npx expo start --go --clear
```

Use an Expo Go client that supports SDK 57. Keep phone and PC on the same Wi-Fi; scan the terminal QR code with Expo Go on Android or the iPhone camera. Select the explicit demo entry on Login. On Windows, iOS can be previewed on a physical iPhone; the iOS Simulator requires macOS.

If LAN discovery is blocked, stop the server with Ctrl+C and use `npx expo start --go --tunnel` (Expo may prompt to install its tunnel helper). Dependency compatibility can be checked with `npx expo install --check`; type checking uses `npm run typecheck`. These are instructions for a later user-authorized run, not checks already performed.
