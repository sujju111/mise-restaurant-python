# Release boundaries

This delivery is a functional pilot foundation. It is not a claim that every module in the long-term plan is complete or that a restaurant can safely go live without validation.

## Implemented

Owner-scoped menus, table visits, current-visit QR, staff ordering, guest pending approval, item preparation/serving, running bills, partial cash recording, print summary, CSV, manual inventory, stock alerts, audit, local persistence, tenant-scoped Rust API and native project/workflow source.

## Before live service

- Replace pilot bearer configuration with managed user authentication, expiry, recovery and rotation. Local demo roles are not security boundaries.
- Verify merchant identity, tax treatment, invoice fields/numbering and receipt rules with the business. The printed bill explicitly is not a tax invoice. Default rates are zero, not a tax/legal recommendation.
- Connect the chosen payment gateway and server-verified webhooks, reconciliation, refunds and receipt lifecycle. Online payment is not functional in this release.
- Validate staff exception policies. Refunds, voids, discounts, amendments after acceptance, session reopening, table transfer/merge and splitting by item are not implemented.
- Add supplier/purchase workflows, recipes and measured fractional ingredient quantities. Existing stock is manual only; sales do not automatically consume ingredients.
- Validate concurrent device use and recovery with actual pilot load, real devices, connectivity, backups, monitoring, error reporting and owner acceptance tests.
- Provide hosted HTTPS API + guest menu when ready. This task intentionally does not deploy either.
- Complete Apple/Android release signing, app-store privacy declarations, actual device testing and store submission. Never ship debug signing for commercial distribution.
- Add owner onboarding and arbitrary restaurant provisioning. Two isolated tenants are supplied to verify separation, not a complete subscription SaaS.

The whole app works locally; customer orders on another phone do not magically sync without a server. The API never trusts local demo roles or browser price totals. Sensitive operations are permission-checked in Rust.
