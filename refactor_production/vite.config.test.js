import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const isDev = process.env.DEV_MODE === 'true' || process.env.VITE_DEV_MODE === 'true'

// Gunakan port 5175 sesuai dengan kebutuhan Anda
export default defineConfig({
  appType: 'spa',
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5175,  // Ganti ke port 5175 agar sesuai dengan URL Anda
    strictPort: false, // Allow other ports if 5175 is occupied
    proxy: isDev ? {
      '/auth': { target: 'http://127.0.0.1:8002', changeOrigin: true },
      '/employees': { target: 'http://127.0.0.1:8002', changeOrigin: true },
      '/payroll': { target: 'http://127.0.0.1:8002', changeOrigin: true },
      '/reports': { target: 'http://127.0.0.1:8002', changeOrigin: true }
    } : {
      '/api/login': {
        target: 'http://localhost:8002',
        changeOrigin: true,
        rewrite: () => '/auth/login'
      },
      '/auth': { target: 'http://127.0.0.1:8002', changeOrigin: true },
      '/employees': { target: 'http://127.0.0.1:8002', changeOrigin: true },
      '/payroll': { target: 'http://127.0.0.1:8002', changeOrigin: true },
      '/reports': { target: 'http://127.0.0.1:8002', changeOrigin: true }
    }
  }
})
