# Local Rust API

Run `npm run setup:api` to generate `.env.local` with random development credentials. This file is ignored by Git and is never bundled into the frontend. Open it locally to copy the owner token, then run `npm run api` in a second terminal. Keep the web dev server running.

Use the staff workspace avatar → Connection settings, API URL `http://localhost:8080`, and one generated token. Tokens remain in memory only. Remote URLs require HTTPS. The API starts empty; it does not import browser sample records.

`MISE_ACCOUNTS` is a JSON array of `{token,tenant,role,name}`. Valid tenants are `juniper`, `ember`; roles are owner, waiter, kitchen, cashier. Every token must be unique and at least 32 characters. This is a bounded pilot configuration, not self-service account registration. Replace this mechanism with expiring identity-provider sessions, token rotation, recovery and managed staff lifecycle before commercial rollout.

Environment:

- `MISE_DATABASE`: SQLite path, default `mise.sqlite`.
- `MISE_BIND`: default `127.0.0.1:8080`; explicitly set `0.0.0.0:8080` behind a secured reverse proxy when hosting.
- `MISE_ORIGINS`: comma-separated allowlist of frontend origins. Default localhost web and Capacitor origins. Never use wildcard origins with staff credentials.
- `MISE_ACCOUNTS`: required account configuration; no default credentials.
- `VITE_MENU_URL`: public HTTPS URL of the guest web app (for example your future menu domain). Native QR sharing stays unavailable until configured, because Capacitor’s localhost origin is not a public website.
- `VITE_API_URL`: optional build-time guest API base URL, required when sharing menu URLs across devices. Use HTTPS in mobile/hosted builds. Rebuild web assets and `npx cap sync` after changing it. This value is public; never place secrets in a `VITE_` variable.

Staff endpoints: `GET /api/me`, `GET /api/state`, `POST /api/command`. Public menu: `GET /api/menu/{slug}`. Current guest visit: `GET /api/guest/{token}`, `POST /api/guest/{token}/command`. `GET /health` exposes health only.

Commands are `{op,data,key,now}`. The API replaces `now` with a server timestamp, derives actor from credentials, and generates the random token for opening a visit. Send the same key when retrying uncertain order/payment submissions. Failures use 401/403/404/422/429 status codes and an `error` message. Monetary amounts use paisa. Database errors omit internal details.

SQLite uses WAL and transactional read-modify-write. Use the SQLite backup API or `sqlite3 mise.sqlite '.backup backup.sqlite'` for a consistent live backup; copying only the main DB file during writes is unsafe. Restore testing, authentication hardening, operational alerts, TLS, capacity tests, recovery procedures and audit retention are release prerequisites.

Local HTTP works in a desktop browser. Native wrappers reject remote cleartext; use a trusted HTTPS endpoint rather than weakening platform transport protections. No backend or domain is deployed by this project.
