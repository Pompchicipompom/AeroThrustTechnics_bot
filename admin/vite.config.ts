import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const backendProxyTarget = process.env.VITE_PROXY_TARGET ?? "http://localhost:8000";

// In production the admin SPA is served under `/admin/` by nginx, so all asset
// URLs in the built `index.html` must be prefixed accordingly. In dev we keep
// the base at `/` so the Vite dev server can proxy `/admin/*` API calls to the
// backend without conflicting with the SPA routes.
export default defineConfig(({ command }) => ({
  base: command === "build" ? "/admin/" : "/",
  plugins: [react()],
  resolve: {
    alias: {
      react: "preact/compat",
      "react-dom": "preact/compat",
      "react-dom/client": "preact/compat",
      "react/jsx-runtime": "preact/jsx-runtime",
      "react/jsx-dev-runtime": "preact/jsx-dev-runtime",
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes("node_modules")) {
            return "vendor";
          }
          return undefined;
        },
      },
    },
  },
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      "/admin": backendProxyTarget,
      "/healthz": backendProxyTarget,
    },
  },
}));
