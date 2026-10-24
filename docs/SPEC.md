# Python edition scope

Preserve the original Mise restaurant visual design, owner-separated menus, kitchen flow, staff workspace, customer QR ordering, billing and native Capacitor projects. Replace Rust domain logic and Axum API with Python FastAPI and SQLite. Provide a browser-local TypeScript engine for offline demo operations.

Critical rules: current-visit QR scoping, explicit guest order approval, menu price snapshots, idempotent payment/order submissions, role checks, integer paisa accounting, kitchen line progression, cash settlement, stock adjustment and atomic writes.

The build pipeline targets a static GitHub Pages demo, Android debug APK and unsigned iOS IPA. Signed distribution, live payments, receipt tax compliance and SaaS onboarding remain outside the pilot scope.
