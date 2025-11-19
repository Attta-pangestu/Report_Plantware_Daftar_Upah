import axios from 'axios'

const TEST_MODE = (import.meta.env?.VITE_DEV_MODE === 'true') || (import.meta.env?.DEV_MODE === 'true')

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
