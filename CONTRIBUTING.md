# Contributing

The Python module `backend/mise/core.py` owns authoritative multi-device billing and business rules. Do not trust the browser or submitted guest prices, roles, session tokens or tenant IDs. `src/engine.ts` is only for an offline single-device demo and should match the Python implementation.

Money is stored in integer **paisa**. Failed operations must not mutate durable state. Keep secrets and any restaurant data out of commits. Run Python domain/API tests, Vue TypeScript checks, web build, Playwright tests and mobile builds before making changes to core operations.

Python tests: `python -m pytest -q backend/tests`. Web tests: `npm run check && npm run build && npm run test:e2e`.
