import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const isDev = process.env.DEV_MODE === 'true' || process.env.VITE_DEV_MODE === 'true'

export default defineConfig({
  appType: 'spa',
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5174,
    strictPort: true, // Always use port 5174
    proxy: isDev ? {
      '/auth': { target: 'http://localhost:8010', changeOrigin: true },
      '/employees': { target: 'http://localhost:8010', changeOrigin: true },
      '/payroll': { target: 'http://localhost:8010', changeOrigin: true },
      '/reports': { target: 'http://localhost:8010', changeOrigin: true }
    } : {
      '/api/login': {
        target: 'http://localhost:8010',
        changeOrigin: true,
        rewrite: () => '/auth/login'
      },
      '/auth': { target: 'http://localhost:8010', changeOrigin: true },
      '/employees': { target: 'http://localhost:8010', changeOrigin: true },
      '/payroll': { target: 'http://localhost:8010', changeOrigin: true },
      '/reports': { target: 'http://localhost:8010', changeOrigin: true }
    }
  }
})
