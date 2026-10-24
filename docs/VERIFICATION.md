# Verification — 24 October 2026

Executed successfully in the development environment:

- Rust formatting and Clippy with warnings treated as errors.
- 13 Rust domain tests: trusted prices; pending approval; duplicate orders; role limits; cross-visit protection; unavailable items; atomic failure; cash retries/overpayment; settlement/closure; service-request coalescing; paisa rounding; stale kitchen taps; unavailable pending item approval.
- 3 Axum API integration tests: authentication/tenant scoping, guest restrictions and sanitized responses, kitchen permissions.
- 2 tests that instantiate and exercise the actual shipped Rust WebAssembly artifact.
- Strict Vue/TypeScript checking and production Vite build.
- Actual Rust HTTP server startup, authenticated tenant state retrieval and empty initial service smoke check.
- Browser interaction journey: seat Table 01 → open current table QR → guest cart → submit pending → staff acceptance → kitchen start → ready → served → cash NPR 320 → zero balance → close visit → table needs cleaning.
- Browser menu separation: edit the Ember menu’s momo name; switch to Juniper and observe its original independent menu.
- Android debug APK and application instrumentation APK compile successfully (`:app:assembleDebug :app:assembleDebugAndroidTest`). APK v2 signature verifies; the embedded engine matches the current compiled WASM bytes.

Prepared but not claimed as executed here:

- Playwright desktop/mobile E2E specifications (four project cases). These run in GitHub Actions; the in-session browser journey above was exercised directly instead.
- Android emulator/device execution of the WebView instrumentation test. Its source is included and CI runs it on an emulator.
- macOS/Xcode simulator build and launch, unsigned device archive and IPA packaging. This Linux environment cannot execute Xcode; the GitHub macOS job defines these steps.
- Signed Android release, signed IPA, TestFlight/App Store distribution and live payment processing. No signing identities or merchant gateway are connected.

No GitHub Actions run is claimed until the public repository is created and the workflow result is observed. Local build success does not certify production readiness. Review `RELEASE.md` before live service.

Review fixes: atomic initialize-or-load prevents reloads from overwriting concurrent local orders; response generation/version checks prevent stale polling from replacing newer staff state; expected kitchen line state rejects concurrent stale taps; native QR sharing requires a public menu URL; expired remote guest sessions invalidate cached visit records.
