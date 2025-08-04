import path from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import tailwindcss from "@tailwindcss/vite";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  base: "/",
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: '0.0.0.0',  // 允许外部设备访问
    port: 3000,    // vite默认端口为5173，这里修改为3000
    proxy: {
      // Proxy API requests to the backend server
      "/api": {
        target: process.env.VITE_BACKEND_URL || "http://127.0.0.1:8000", // 支持环境变量配置后端地址
        changeOrigin: true,
        secure: false, // 开发环境可以禁用SSL验证
      },
    },
  },
});
