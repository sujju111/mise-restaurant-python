# Verification

The supplied Python conversion kit passed **15 local tests** for role checks, restaurant isolation, guest scope, trusted menu prices, idempotent retries, cash settlement, visit closure, kitchen transitions, atomic failure and API body limits. The GitHub-port code should be verified independently by the GitHub Actions test workflow after upload.

Run `python -m pytest -q backend/tests`, `npm run check`, `npm run build`, and `npm run test:e2e` after installing dependencies. The browser and native CI jobs must complete successfully before packaged artifacts are relied on.

Not yet claimed: live hosted Python backend, browser Playwright success on every target, device field testing, App Store signing or production/security certification. A local pilot isn't an unattended commercial accounting system.
