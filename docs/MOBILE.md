# Android and iOS

Both native projects are generated with Capacitor 8. The local TypeScript demo engine runs inside the WebView. The shared Python API runs separately on a server.

## Android

Requirements: Node 22+, Java 21, Android SDK platform 36 and build tools 36.0.0. Use Android Studio or set `ANDROID_HOME`.

```sh
npm ci
npm run build
npx cap sync android
cd android
./gradlew :app:assembleDebug
./gradlew :app:connectedDebugAndroidTest
```

Windows: use `gradlew.bat`. Install the result from `android/app/build/outputs/apk/debug/app-debug.apk` on a test device. This is a debug build, not a store release. Release signing needs a private keystore kept outside Git. Application ID: `com.mise.restaurant`.

The instrumentation test launches the real MainActivity, waits for the WebView and checks that the Vue workspace and browser engine have booted. The shared business and API tests run separately in CI. No real payments or cloud backend are required.

## iOS

Requires macOS and Xcode 26+. Open `ios/App/App.xcodeproj`, select your Apple team and change the bundle ID if necessary. Run on a simulator without distribution credentials. This project uses Capacitor’s Swift Package Manager integration.

```sh
npm run build
npx cap sync ios
npx cap open ios
```

CI builds and launches a simulator app, archives an unsigned device app, and packages `Mise-unsigned.ipa`. This IPA cannot be installed until signed with a matching Apple certificate/provisioning profile. It is not TestFlight-ready. For a signed installable IPA, archive/export in Xcode with your team and an appropriate distribution method. This cannot be completed without your Apple signing setup.

`ci.yml` has an iOS launch smoke check, not an XCTest interaction suite. Desktop/mobile web E2E tests exercise the application interaction flow. Extend native device tests before distribution; test iOS WKWebView persistence, printer integration, background/resume and Android low-memory recovery on actual restaurant devices.

Set both `VITE_MENU_URL` (the public guest website) and `VITE_API_URL` when you later enable cross-device QR ordering. Without a public guest website, native QR sharing is unavailable and the on-device guest preview remains usable.

All demo food images, fonts are bundled. The native app can run local workflows without an internet connection. Shared staff/guest service requires the reachable API and web menu; no offline multi-device synchronization is promised.
