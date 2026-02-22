import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  base: "/admin/",
  plugins: [react()],
  build: {
    outDir: "../admin-dist",
    emptyOutDir: true,
    sourcemap: false,
    minify: "esbuild"
  },
  server: {
    host: true,
    port: 5174
  }
});
