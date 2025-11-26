import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Production configuration using 10.0.0.110
const PRODUCTION_IP = '10.0.0.110'
const PRODUCTION_BACKEND_PORT = '8002'
const PRODUCTION_FRONTEND_PORT = '5176'

const backendTarget = `http://${PRODUCTION_IP}:${PRODUCTION_BACKEND_PORT}`

console.log('🚀 Production Configuration:')
console.log(`📡 Backend Target: ${backendTarget}`)
console.log(`🌐 Frontend will run on: http://${PRODUCTION_IP}:${PRODUCTION_FRONTEND_PORT}`)

export default defineConfig({
  appType: 'spa',
  plugins: [react()],
  define: {
    // Production environment variables
    'process.env.NODE_ENV': JSON.stringify('production'),
    'process.env.VITE_PRODUCTION_MODE': JSON.stringify('true'),
    'process.env.VITE_BACKEND_URL': JSON.stringify(backendTarget)
  },
  server: {
    host: '0.0.0.0', // Allow access from any IP
    port: PRODUCTION_FRONTEND_PORT,
    strictPort: true, // Use specific port for production
    cors: true,
    headers: {
      // Production CORS headers
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization'
    },
    proxy: {
      '/auth': {
        target: backendTarget,
        changeOrigin: true,
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('❗ Proxy error (auth):', err.message);
          });
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log(`📤 Auth Request: ${req.method} ${req.url} → ${backendTarget}`);
          });
        },
      },
      '/employees': {
        target: backendTarget,
        changeOrigin: true,
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('❗ Proxy error (employees):', err.message);
          });
        },
      },
      '/payroll': {
        target: backendTarget,
        changeOrigin: true,
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('❗ Proxy error (payroll):', err.message);
          });
        },
      },
      '/reports': {
        target: backendTarget,
        changeOrigin: true,
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('❗ Proxy error (reports):', err.message);
          });
        },
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false, // Disable sourcemaps for production
    minify: 'terser',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          agGrid: ['ag-grid-community', 'ag-grid-enterprise', 'ag-grid-react'],
          utils: ['axios', 'js-cookie']
        }
      }
    }
  }
})