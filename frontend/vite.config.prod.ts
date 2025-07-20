import path from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import tailwindcss from "@tailwindcss/vite";

// Production configuration without TypeScript checking
export default defineConfig({
  plugins: [react(), tailwindcss()],
  base: "/",
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  build: {
    outDir: "dist",
    // Skip TypeScript checking during build
    rollupOptions: {
      onwarn(warning, warn) {
        // Ignore TypeScript warnings during build
        if (warning.code === 'TYPESCRIPT') return;
        warn(warning);
      }
    }
  },
  esbuild: {
    // Disable TypeScript type checking
    tsconfigRaw: {}
  }
});