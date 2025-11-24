import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const isDev = process.env.DEV_MODE === 'true' || process.env.VITE_DEV_MODE === 'true'

export default defineConfig({
  appType: 'spa',
  plugins: [react()],
  define: {
    // Force disable cache for development
    'process.env.VITE_DISABLE_CACHE': JSON.stringify('true'),
    'process.env.VITE_DEV_MODE': JSON.stringify('true')
  },
  server: {
    host: '0.0.0.0',
    port: 5174,
    strictPort: false, // Allow other ports if 5174 is occupied
    headers: {
      // Disable browser caching for development
      'Cache-Control': 'no-cache, no-store, must-revalidate',
      'Pragma': 'no-cache',
      'Expires': '0'
    },
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
