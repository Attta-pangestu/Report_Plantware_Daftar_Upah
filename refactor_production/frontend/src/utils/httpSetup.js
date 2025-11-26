import axios from 'axios'

const TEST_MODE = (import.meta.env?.VITE_DEV_MODE === 'true') || (import.meta.env?.DEV_MODE === 'true')

// Auto-detect if we're in network mode and get the correct backend URL
const getBackendURL = () => {
  // If custom backend URL is provided, use it
  if (import.meta.env?.VITE_BACKEND_URL) {
    return import.meta.env.VITE_BACKEND_URL
  }

  const _port = (import.meta.env?.VITE_BACKEND_PORT || import.meta.env?.BACKEND_PORT || '8002')
  let _host = (import.meta.env?.VITE_BACKEND_HOST || import.meta.env?.BACKEND_HOST)

  // If no custom host is specified, detect if we should use the current host IP
  if (!_host || _host === 'localhost') {
    // Check if we're accessing from an IP address (not localhost)
    const currentHost = window.location.hostname
    if (currentHost !== 'localhost' && currentHost !== '127.0.0.1') {
      _host = currentHost
      console.log(`🌐 Detected network access, using backend: ${_host}`)
    } else {
      _host = 'localhost'
    }
  }

  return `http://${_host}:${_port}`
}

const _url = getBackendURL()
axios.defaults.baseURL = _url

console.log('🔗 HTTP Setup - Backend URL:', _url)
console.log('🌐 Current Frontend Host:', window.location.hostname)

// Enable credentials for all requests (important for cookies)
axios.defaults.withCredentials = true

axios.interceptors.request.use(async (config) => {
  try {
    const start = Date.now()
    config.meta = Object.assign({}, config.meta, { start })
    const u = (config.baseURL || '') + (config.url || '')
    const m = (config.method || 'get').toUpperCase()
    const p = config.params || {}
    console.log(`[HTTP] -> ${m} ${u}`, { params: p, headers: Object.keys(config.headers || {}) })
  } catch (_) {}
  return config
})

axios.interceptors.response.use(
  (res) => {
    try {
      const start = res.config?.meta?.start || Date.now()
      const dur = Date.now() - start
      const u = (res.config?.baseURL || '') + (res.config?.url || '')
      const m = (res.config?.method || 'get').toUpperCase()
      console.log(`[HTTP] <- ${m} ${u} ${res.status} ${dur}ms`, { length: Array.isArray(res.data) ? res.data.length : undefined })
    } catch (_) {}
    return res
  },
  async (error) => {
    try {
      const cfg = error.config || {}
      const u = (cfg.baseURL || '') + (cfg.url || '')
      const m = (cfg.method || 'get').toUpperCase()
      const start = cfg.meta?.start || Date.now()
      const dur = Date.now() - start
      console.error(`[HTTP] !! ${m} ${u} ${error?.response?.status || 'ERR'} ${dur}ms`, { message: error.message })
    } catch (_) {}
    return Promise.reject(error)
  }
)
