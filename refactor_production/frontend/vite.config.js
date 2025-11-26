import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const isDev = process.env.DEV_MODE === 'true' || process.env.VITE_DEV_MODE === 'true'

// Get backend host from environment variables or use default
const getBackendHost = () => {
  // Check for custom backend host in environment variables
  const customHost = process.env.VITE_BACKEND_HOST || process.env.BACKEND_HOST
  const customPort = process.env.VITE_BACKEND_PORT || process.env.BACKEND_PORT || '8002'

  if (customHost) {
    return `http://${customHost}:${customPort}`
  }

  // For development, try to detect the local IP address for network access
  // or fallback to localhost for local development
  if (isDev) {
    return `http://localhost:${customPort}`
  }

  // Default to localhost with current backend port
  return `http://localhost:${customPort}`
}

const backendTarget = getBackendHost()

console.log('Proxy configuration:', {
  isDev,
  backendTarget,
  envVars: {
    VITE_BACKEND_HOST: process.env.VITE_BACKEND_HOST,
    BACKEND_HOST: process.env.BACKEND_HOST,
    VITE_BACKEND_PORT: process.env.VITE_BACKEND_PORT,
    BACKEND_PORT: process.env.BACKEND_PORT,
    DEV_MODE: process.env.DEV_MODE,
    VITE_DEV_MODE: process.env.VITE_DEV_MODE
  }
})

export default defineConfig({
  appType: 'spa',
  plugins: [react()],
  define: {
    // Force disable cache for development
    'process.env.VITE_DISABLE_CACHE': JSON.stringify('true'),
    'process.env.VITE_DEV_MODE': JSON.stringify('true')
  },
  server: {
    host: '0.0.0.0', // Allow access from any IP
    port: 5174,
    strictPort: false, // Allow other ports if 5174 is occupied
    cors: true, // Enable CORS for all origins
    headers: {
      // Disable browser caching for development
      'Cache-Control': 'no-cache, no-store, must-revalidate',
      'Pragma': 'no-cache',
      'Expires': '0',
      // Enable CORS headers for external access
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
            console.log('proxy error', err);
          });
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log('Sending Request to the Target:', req.method, req.url);
          });
          proxy.on('proxyRes', (proxyRes, req, _res) => {
            console.log('Received Response from the Target:', proxyRes.statusCode, req.url);
          });
        },
      },
      '/employees': {
        target: backendTarget,
        changeOrigin: true,
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('proxy error', err);
          });
        },
      },
      '/payroll': {
        target: backendTarget,
        changeOrigin: true,
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('proxy error', err);
          });
        },
      },
      '/reports': {
        target: backendTarget,
        changeOrigin: true,
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('proxy error', err);
          });
        },
      }
    }
  }
})
