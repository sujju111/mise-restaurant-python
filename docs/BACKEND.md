# Mise Python API

This edition replaces Rust/Axum with **Python FastAPI + SQLite** while retaining these endpoints:

- Staff: `GET /api/me`, `GET /api/state`, `POST /api/command` (bearer token required).
- Public menu: `GET /api/menu/{slug}`.
- Guest: `GET /api/guest/{token}`, `POST /api/guest/{token}/command`.
- Health: `GET /health`.

## Local setup

Requires Python 3.11+ and Node.js 22+. Install dependencies with `python -m pip install -r backend/requirements-dev.txt`, then run `python backend/setup_accounts.py` to generate ignored `.env.local` strong staff credentials. Start API with `npm run api` and Vue with `npm run dev` in a separate terminal.

Use app Connection settings, API URL `http://localhost:8080`, and a generated staff token. The API seeds two separate restaurants, but starts with no dining visits. It does not import browser IndexedDB demo state or automatically migrate existing live databases.

`MISE_ACCOUNTS`: JSON list of token, tenant, role, name. `MISE_DATABASE`: SQLite database file path. `MISE_ORIGINS`: explicit allowed frontend origins. `VITE_API_URL` and `VITE_MENU_URL` are **public frontend settings**, not secrets; for remote/native guest use they must point to HTTPS services.

Commands take `{op, data, key, now}`; Python replaces timestamps and generates random current-visit tokens. Monetary values are integer paisa. Writes commit atomically; repeated accepted order and payment retry keys do not double-charge. Server enforces staff role and restaurant tenancy and limits requests to 64 KiB; guest API is rate-limited and returns only active visit information.

**Production gap:** This is a bounded pilot server. Set up real identity management, expiry/rotation, TLS, backups and restore drills, observability, merchant payment validation and concurrency/load tests before commercial use. Cash records are not online payment processing. GitHub Pages cannot run the API.
