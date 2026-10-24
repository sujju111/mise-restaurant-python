# Mise Python architecture

- **UI:** Vue 3 + Vuetify + TypeScript + Vite.
- **Mobile:** Capacitor Android and iOS wrappers using web assets.
- **Python API:** FastAPI in `backend/mise/api.py`, retaining the original Rust API endpoint paths and data shapes.
- **Business rules:** `backend/mise/core.py`, including role enforcement, menu price snapshots, order approval, kitchen transitions, integer paisa billing, cash idempotency and visit closure.
- **Persistence:** SQLite in WAL mode. The pilot stores each restaurant aggregate as JSON and performs read-modify-write in `BEGIN IMMEDIATE` transactions.
- **Browser demo:** `src/engine.ts` executes demo commands on IndexedDB state without Rust/WASM. Demo role selection is not server authentication.

Remote staff roles and tenant scope are derived from server credentials. Guest QR tokens grant access only to an active table visit; closing a visit invalidates its guest link. Demo restaurants Juniper and Ember have separate menus and service data. The local browser demo does not synchronize across different devices.

For multi-device use host the Python API with HTTPS and configure the public guest web URL. GitHub Pages serves only a static demo. Commercial SaaS requires normalized storage, tenant onboarding, credential lifecycle, schema migrations, tested concurrency and monitoring.
