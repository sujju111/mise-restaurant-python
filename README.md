# Mise

A thoughtful restaurant workspace built with **Vue 3 + Vuetify, Rust, SQLite and Capacitor**. The guest menu is a responsive website; staff can use the same application on web, Android or iOS.

**Status: working local demo and pilot foundation, not certified for unattended production use.** The browser demo can be published to GitHub Pages; the Rust API is not deployed. The local browser demo uses the actual Rust business engine compiled to WebAssembly, with durable IndexedDB transactions. The optional API uses that same crate and a transactional SQLite database. No parallel JavaScript billing implementation.

## Web demo on GitHub Pages

[Open the live Mise demo](https://sujju111.github.io/mise-restaurant/).

The Pages workflow publishes the browser-local demo. Every visitor gets their own local workspace; it does not host the Rust API or synchronize different devices. Use the included API when you later connect shared restaurant service.

## Try it

Install Node.js 22+. The compiled WebAssembly engine is included, so Rust is optional for simply opening the demo.

```sh
npm ci
npm run dev
```

Open the URL Vite prints (normally `http://localhost:5173`). The first visit loads a clearly labelled sample service. To start empty, use **Settings → Clear sample service**.

1. Select an available table and open a dining session.
2. Use **Table QR → Open this table’s guest menu**.
3. Add dishes, review the cart and submit for staff approval.
4. Return to staff, accept the request, then progress each item in **Kitchen**.
5. Mark ready food served. Open **Bill**, record received cash, then close the visit.
6. Mark the table clean before seating a new party. The previous visit’s QR expires.
7. Edit prices and availability in **Menu studio**. Switch between Juniper House and Ember Kitchen to verify owner-specific menus and records.

Local mode is a real single-device demo, with updates shared across tabs on the same origin. It is **not a multi-device sync service**. Local role switching is a testing convenience, not login. The server requires staff bearer credentials and derives role and tenant from those credentials.

## Included

- Separate restaurant identity, menu, pricing, availability and operational records.
- Table grid, dining sessions, current-visit QR and repeated order rounds.
- Staff orders and guest requests with explicit acceptance or rejection.
- Item-level kitchen preparation and serving states.
- Integer minor-unit totals, configurable tax/service basis points, running bills, partial cash payments, duplicate-payment protection and overpayment rejection.
- Cashier bills, print stylesheet and payment CSV export.
- Waiter/bill requests with repeated-tap coalescing.
- Owner-only menu/settings/manual stock adjustments, stock alerts and audit events.
- Rust API with SQLite transactions, bearer roles, tenant scoping, body limits, explicit CORS and guest request limits.
- Android and iOS native source projects and GitHub Actions definitions.
- Rust domain/API tests, tests against the shipped WASM artifact and desktop/mobile Playwright specifications.

## Build and check

To change Rust logic, install stable Rust and the WASM target:

```sh
rustup target add wasm32-unknown-unknown
npm run wasm
npm run check
npm run build
```

The shared menu seed lives in `crates/core/src/seed.json`; the frontend imports it directly. All prices are integer paisa (NPR × 100), all quantities are whole units, tax and service are independently calculated on subtotal and rounded half-up to paisa. Confirm local tax treatment before live use.

See [backend setup](docs/BACKEND.md), [mobile builds](docs/MOBILE.md), [architecture](docs/ARCHITECTURE.md), [verification](docs/VERIFICATION.md) and [release boundaries](docs/RELEASE.md).

## GitHub

The `.github/workflows/ci.yml` workflow runs on push, pull request and manual dispatch. It checks Rust/web code, builds a debug APK, runs an Android WebView instrumentation test, builds and launches an iOS simulator app, and packages an **unsigned IPA**. It does not deploy or publish to an app store.

An unsigned IPA is an archive for signing, not an installable iPhone app. A store release needs your Apple Developer identity, provisioning and signing. The APK produced by this workflow is for testing and uses a debug key.

If GitHub creation is unavailable in your current connected tool, this checkout is ready to upload to a new public repository with:

```sh
git init -b main
git add .
git commit -m "Initial Mise restaurant application"
gh repo create mise-restaurant --public --source=. --remote=origin --push
```

Requires GitHub CLI authentication on your own computer. No access token belongs in this repository.

## License and assets

Original application code is MIT. Third-party packages retain their own licenses. Demo food photography is bundled from Unsplash; it is illustrative and does not represent each named dish exactly. Fonts are bundled for offline/native use. See [third-party notices](docs/THIRD_PARTY.md).
