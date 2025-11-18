import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const isDev = process.env.DEV_MODE === 'true' || process.env.VITE_DEV_MODE === 'true'

export default defineConfig({
  appType: 'spa',
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5174,
    strictPort: false, // Allow other ports if 5174 is occupied
    proxy: isDev ? {
      '/auth': { target: 'http://localhost:8002', changeOrigin: true },
      '/employees': { target: 'http://localhost:8002', changeOrigin: true },
      '/payroll': { target: 'http://localhost:8002', changeOrigin: true },
      '/reports': { target: 'http://localhost:8002', changeOrigin: true }
    } : {
      '/api/login': {
        target: 'http://localhost:8002',
        changeOrigin: true,
        rewrite: () => '/auth/login'
      },
      '/auth': { target: 'http://localhost:8002', changeOrigin: true },
      '/employees': { target: 'http://localhost:8002', changeOrigin: true },
      '/payroll': { target: 'http://localhost:8002', changeOrigin: true },
      '/reports': { target: 'http://localhost:8002', changeOrigin: true }
    }
  }
})
