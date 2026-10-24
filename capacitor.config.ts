import type { CapacitorConfig } from "@capacitor/cli";
const config: CapacitorConfig = {
  appId: "com.mise.restaurant",
  appName: "Mise",
  webDir: "dist",
  android: { allowMixedContent: false },
  ios: { contentInset: "always" },
  backgroundColor: "#f6f5f0",
};
export default config;
