import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const isDev = process.env.DEV_MODE === 'true'

export default defineConfig({
  appType: 'spa',
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5174,
    strictPort: true, // Always use port 5174
    proxy: isDev ? {
      // In dev mode, only proxy API endpoints, skip auth
      '/employees': { target: 'http://localhost:8000', changeOrigin: true },
      '/payroll': { target: 'http://localhost:8000', changeOrigin: true },
      '/reports': { target: 'http://localhost:8000', changeOrigin: true }
    } : {
      // Production mode with full auth
      '/api/login': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: () => '/auth/login'
      },
      '/auth': { target: 'http://localhost:8000', changeOrigin: true },
      '/employees': { target: 'http://localhost:8000', changeOrigin: true },
      '/payroll': { target: 'http://localhost:8000', changeOrigin: true },
      '/reports': { target: 'http://localhost:8000', changeOrigin: true }
    }
  }
})
