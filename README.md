# Mise — Python edition

A restaurant workspace with **Python (FastAPI) + SQLite** backend, **Vue 3 + Vuetify** frontend, and **Capacitor** Android/iOS wrappers. Ported from [sujju111/mise-restaurant](https://github.com/sujju111/mise-restaurant), which remains unchanged.

**Status:** functional local-demo/pilot foundation; **not production certified**. The offline, single-device web demo uses a TypeScript compatibility engine; shared multi-device operations use the authoritative Python API. This edition has no Rust or WebAssembly dependency.

## Features

Restaurant-specific menus, QR table visits, guest orders requiring staff acceptance, kitchen item preparation and serving, cash billing, integer paisa prices with tax/service rates, idempotent payment retries, manual stock adjustments, staff permissions and tenant-separated SQLite state.

## Getting started (Windows PowerShell)

Install Python 3.11+ and Node.js 22+, then run:

```powershell
git clone https://github.com/sujju111/mise-restaurant-python.git
cd mise-restaurant-python
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
npm ci
npm run dev
```

Visit the Vite address, normally http://localhost:5173. Browser demo mode works without starting the Python API.

For shared API mode, open another terminal in the project directory:

```powershell
python backend/setup_accounts.py
npm run api
```

Copy your **Juniper owner** token from the printed output, then use the app's **Connection settings** and enter `http://localhost:8080` with that token. The API starts with empty visits and independent seeded menus.

## Test and build

```powershell
python -m pytest -q backend/tests
npm run check
npm run build
npx playwright install chromium
npm run test:e2e
npm run native:sync
```

A GitHub Actions workflow runs Python/domain API tests, TypeScript/React-free Vue checks, Playwright web tests, Android debug packaging, and iOS simulator/unsigned IPA steps. Confirm workflow results in Actions before trusting generated artifacts.

**GitHub Pages serves a browser-only demo. It cannot host FastAPI or synchronize restaurant devices.** Real QR ordering across phones requires a separately hosted HTTPS Python server and the `VITE_API_URL` / `VITE_MENU_URL` configuration. A debug APK isn't a store release; an unsigned IPA needs Apple Developer signing to install on iPhones.

See [backend](docs/BACKEND.md), [architecture](docs/ARCHITECTURE.md), [mobile](docs/MOBILE.md), [verification](docs/VERIFICATION.md) and [release boundaries](docs/RELEASE.md). License: MIT original application; third-party assets/dependencies retain their own notices.
