# Contributing

Rust owns business rules; do not reimplement billing or authorization in Vue. Store prices in integer paisa. Test public command/API boundaries with known literal results. Never trust guest prices, roles or tenant IDs. A failed command must not change durable state. Keep credentials and real restaurant data outside Git.

Run `cargo fmt --all`, `cargo clippy --workspace --all-targets -- -D warnings`, `cargo test --workspace`, `npm run wasm`, `npm run typecheck`, `npm test`, `npm run build` and the desktop/mobile E2E tests before merging changes to operational flows. Keep UI controls accessible by name, clear about saving/error states and responsive to restaurant devices. New features need explicit scope and review.
