import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  appType: 'spa',
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: false,
    proxy: {
      '/api/login': {
        target: 'http://localhost:8003',
        changeOrigin: true,
        rewrite: () => '/auth/login'
      },
      '/auth': { target: 'http://localhost:8003', changeOrigin: true },
      '/employees': { target: 'http://localhost:8003', changeOrigin: true },
      '/payroll': { target: 'http://localhost:8003', changeOrigin: true },
      '/reports': { target: 'http://localhost:8003', changeOrigin: true }
    }
  }
})
