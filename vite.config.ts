import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
export default defineConfig({
  plugins: [vue()],
  base: process.env.VITE_BASE_PATH || "/",
  server: { host: "0.0.0.0", allowedHosts: ["terminal.local"] },
  build: { target: "es2022", chunkSizeWarningLimit: 1000 },
});
